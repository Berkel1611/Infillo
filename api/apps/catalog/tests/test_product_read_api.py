from datetime import timedelta
from decimal import Decimal

import pytest
from django.conf import settings
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from apps.catalog.models import Category, CategoryModerator, Product, ProductVariant

pytestmark = pytest.mark.django_db

DESCRIPTION = {
    "type": "doc",
    "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Opis"}]}],
}


def make(name: str, parent: Category | None = None) -> Category:
    return Category.objects.create(name=name, parent=parent)


def make_product(
    category: Category,
    name: str = "Figurka",
    published: bool = True,
    prices: tuple[Decimal, ...] = (Decimal("49.00"),),
    stock: int = 1,
    made_to_order: bool = False,
) -> Product:
    product = Product.objects.create(
        name=name, category=category, is_published=published, description=DESCRIPTION
    )
    for index, price in enumerate(prices):
        ProductVariant.objects.create(
            product=product,
            price=price,
            size=f"size{index}",
            stock=stock,
            made_to_order=made_to_order,
        )
    return product


def names(response) -> list[str]:
    return [item["name"] for item in response.json()["results"]]


def code(response) -> str:
    return response.json()["code"]


# --- GET /products ---


def test_list_published_only_even_for_admin(login, administrator):
    category = make("Dom")
    make_product(category, "Opublikowany")
    make_product(category, "Szkic", published=False)

    for client in (APIClient(), login(administrator)):
        response = client.get("/products")
        assert response.status_code == 200
        assert names(response) == ["Opublikowany"]


def test_list_shape_and_envelope(login, moderator):
    category = make("Dom")
    make_product(category, "Figurka", prices=(Decimal("59.90"), Decimal("49.00")))

    body = login(moderator).get("/products").json()

    assert set(body) == {"count", "next", "previous", "results"}
    row = body["results"][0]
    assert set(row) == {"id", "name", "category", "price_from", "availability"}
    assert row["category"] == {"id": category.id, "name": "Dom"}
    assert row["price_from"] == "49.00"
    assert row["availability"] == "AVAILABLE"


def test_price_from_and_availability_in_row():
    category = make("Dom")
    make_product(category, "Brak", stock=0)
    make_product(category, "Na zamówienie", stock=0, made_to_order=True)
    made = Product.objects.create(name="Bez wariantów", category=category, is_published=True)

    rows = {r["name"]: r for r in APIClient().get("/products").json()["results"]}

    assert rows["Brak"]["availability"] == "OUT_OF_STOCK"
    assert rows["Na zamówienie"]["availability"] == "MADE_TO_ORDER"
    assert rows[made.name]["price_from"] is None
    assert rows[made.name]["availability"] == "OUT_OF_STOCK"


def test_newest_first_ordering():
    category = make("Dom")
    for name in ("A", "B", "C"):
        make_product(category, name)

    assert names(APIClient().get("/products")) == ["C", "B", "A"]


def test_category_filter_includes_descendants():
    root = make("Dom")
    child = make("Organizery", root)
    other = make("Figurki")
    make_product(root, "W korzeniu")
    make_product(child, "W podkategorii")
    make_product(other, "Gdzie indziej")

    in_root = APIClient().get(f"/products?category={root.id}")
    in_child = APIClient().get(f"/products?category={child.id}")

    assert sorted(names(in_root)) == ["W korzeniu", "W podkategorii"]
    assert names(in_child) == ["W podkategorii"]


def test_unknown_category_404():
    response = APIClient().get("/products?category=999999")
    assert (response.status_code, code(response)) == (404, "CATEGORY_NOT_FOUND")


@pytest.mark.parametrize("query", ["category=abc", "category=1.5", "search=" + "x" * 101])
def test_invalid_query_400(query):
    response = APIClient().get(f"/products?{query}")
    assert (response.status_code, code(response)) == (400, "VALIDATION_ERROR")


def test_empty_filters_are_ignored():
    make_product(make("Dom"), "Smok")

    assert names(APIClient().get("/products?category=&search=")) == ["Smok"]


def test_search_by_name():
    category = make("Dom")
    make_product(category, "Smok czerwony")
    make_product(category, "Pudełko")

    assert names(APIClient().get("/products?search=SMOK")) == ["Smok czerwony"]
    assert names(APIClient().get("/products?search=")) == ["Pudełko", "Smok czerwony"]
    assert names(APIClient().get("/products?search=brak")) == []


def test_search_treats_special_characters_literally():
    category = make("Dom")
    make_product(category, "Smok 100%")
    make_product(category, "Smok")

    # "%" and "_" are LIKE wildcards in SQL; Django escapes them for icontains
    assert names(APIClient().get("/products?search=100%25")) == ["Smok 100%"]
    assert names(APIClient().get("/products?search=_mok")) == []


def test_pagination_and_page_size_cap():
    category = make("Dom")
    for index in range(25):
        make_product(category, f"P{index:02d}")

    first = APIClient().get("/products").json()
    assert first["count"] == 25 and len(first["results"]) == 20 and first["next"]
    assert len(APIClient().get("/products?page=2").json()["results"]) == 5
    assert len(APIClient().get("/products?page_size=10").json()["results"]) == 10
    assert len(APIClient().get("/products?page_size=1000").json()["results"]) == 25  # cap is 100


def test_page_size_cap_is_100():
    category = make("Dom")
    Product.objects.bulk_create(
        [Product(name=f"P{i}", category=category, is_published=True) for i in range(105)]
    )

    response = APIClient().get("/products?page_size=1000").json()

    assert response["count"] == 105 and len(response["results"]) == 100


def test_list_without_n_plus_one(django_assert_max_num_queries):
    category = make("Dom")
    for index in range(20):
        make_product(category, f"P{index:02d}", prices=(Decimal("10.00"), Decimal("20.00")))

    with django_assert_max_num_queries(5):
        response = APIClient().get("/products")

    assert len(response.json()["results"]) == 20


def test_list_with_expired_cookie_200(regular_user):
    # Review Focus 2: a stale cookie must not turn the public catalog into a 401
    expired = AccessToken.for_user(regular_user)
    expired.set_exp(lifetime=-timedelta(minutes=1))
    client = APIClient()
    client.cookies[settings.AUTH_COOKIE_NAME] = str(expired)

    assert client.get("/products").status_code == 200


# --- GET /products/{id} ---


def test_detail_published_public():
    root = make("Dom")
    child = make("Organizery", root)
    product = make_product(child, "Figurka", prices=(Decimal("30.00"), Decimal("20.00")))

    response = APIClient().get(f"/products/{product.id}")

    assert response.status_code == 200
    body = response.json()
    assert body["description"] == DESCRIPTION
    assert [c["name"] for c in body["category_path"]] == ["Dom", "Organizery"]
    assert [v["price"] for v in body["variants"]] == ["30.00", "20.00"]
    assert body["price_from"] == "20.00"


def test_detail_draft_visibility(login, moderator, administrator, regular_user):
    assigned, other = make("Dom"), make("Figurki")
    CategoryModerator.objects.create(category=assigned, moderator=moderator)
    mine = make_product(assigned, "Mój szkic", published=False)
    foreign = make_product(other, "Cudzy szkic", published=False)

    guest = APIClient().get(f"/products/{mine.id}")
    assert (guest.status_code, code(guest)) == (404, "PRODUCT_NOT_FOUND")
    assert login(regular_user).get(f"/products/{mine.id}").status_code == 404
    assert login(moderator).get(f"/products/{mine.id}").status_code == 200
    # a moderator outside the category gets the same answer as for a product that does not exist
    hidden = login(moderator).get(f"/products/{foreign.id}")
    missing = login(moderator).get("/products/999999")
    assert (hidden.status_code, hidden.json()) == (missing.status_code, missing.json())
    assert login(administrator).get(f"/products/{foreign.id}").status_code == 200


def test_detail_unknown_or_malformed_id_404():
    for url in ("/products/999999", "/products/abc"):
        response = APIClient().get(url)
        assert (response.status_code, code(response)) == (404, "PRODUCT_NOT_FOUND")


def test_category_path_order():
    one = make("Jeden")
    two = make("Dwa", one)
    three = make("Trzy", two)
    product = make_product(three)

    path = APIClient().get(f"/products/{product.id}").json()["category_path"]

    assert [item["id"] for item in path] == [one.id, two.id, three.id]


# --- GET /products/managed ---


def test_managed_scope_includes_drafts(login, moderator, administrator):
    assigned, child, other = make("Dom"), None, make("Figurki")
    child = make("Organizery", assigned)
    CategoryModerator.objects.create(category=assigned, moderator=moderator)
    make_product(assigned, "Opublikowany")
    make_product(child, "Szkic w podkategorii", published=False)
    make_product(other, "Poza zakresem", published=False)

    as_moderator = login(moderator).get("/products/managed")
    as_admin = login(administrator).get("/products/managed")

    assert sorted(names(as_moderator)) == ["Opublikowany", "Szkic w podkategorii"]
    assert len(names(as_admin)) == 3
    rows = {r["name"]: r for r in as_moderator.json()["results"]}
    assert rows["Opublikowany"]["is_published"] is True
    assert rows["Szkic w podkategorii"]["is_published"] is False


def test_managed_category_filter_and_pagination(login, administrator):
    one, two = make("Dom"), make("Figurki")
    for index in range(3):
        make_product(one, f"A{index}", published=False)
    make_product(two, "B")
    client = login(administrator)

    assert sorted(names(client.get(f"/products/managed?category={one.id}"))) == ["A0", "A1", "A2"]
    assert client.get("/products/managed?page_size=2").json()["count"] == 4
    assert len(client.get("/products/managed?page_size=2").json()["results"]) == 2
    missing = client.get("/products/managed?category=999999")
    assert (missing.status_code, code(missing)) == (404, "CATEGORY_NOT_FOUND")


def test_managed_forbidden_for_user_401_for_guest(login, regular_user):
    assert APIClient().get("/products/managed").status_code == 401
    assert login(regular_user).get("/products/managed").status_code == 403


def test_managed_is_not_swallowed_by_the_detail_route(login, administrator):
    # "/products/managed" must reach the list action, not look for a product with id "managed"
    response = login(administrator).get("/products/managed")
    assert response.status_code == 200 and "results" in response.json()


def test_moderator_who_lost_role_sees_nothing_managed(login, moderator):
    from django.contrib.auth.models import Group

    from apps.accounts.models import MODERATORS_GROUP

    category = make("Dom")
    CategoryModerator.objects.create(category=category, moderator=moderator)
    make_product(category, published=False)
    moderator.groups.remove(Group.objects.get(name=MODERATORS_GROUP))

    assert login(moderator).get("/products/managed").status_code == 403
