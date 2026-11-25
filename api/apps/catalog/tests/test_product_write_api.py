from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.catalog.models import Category, CategoryModerator, Product, ProductVariant

pytestmark = pytest.mark.django_db

DESCRIPTION = {
    "type": "doc",
    "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Opis"}]}],
}


def make(name: str, parent: Category | None = None) -> Category:
    return Category.objects.create(name=name, parent=parent)


def assign(category: Category, user) -> None:
    CategoryModerator.objects.create(category=category, moderator=user)


def payload(category: Category, **kwargs) -> dict:
    return {"name": "Figurka smoka", "category_id": category.id, **kwargs}


def variant(**kwargs) -> dict:
    return {"color": "czerwony", "price": "49.00", "stock": 2, **kwargs}


def make_product(category: Category, published: bool = False, **kwargs) -> Product:
    product = Product.objects.create(
        name="Istniejący", category=category, is_published=published, description=DESCRIPTION
    )
    ProductVariant.objects.create(product=product, price=Decimal("10.00"), **kwargs)
    return product


def code(response) -> str:
    return response.json()["code"]


def field_errors(response) -> list[dict]:
    return response.json()["fields"]


# --- roles and scope ---


def test_create_roles(login, regular_user, moderator, administrator):
    assigned, other = make("Dom"), make("Figurki")
    assign(assigned, moderator)

    guest = APIClient().post("/products", payload(assigned), format="json")
    user = login(regular_user).post("/products", payload(assigned), format="json")
    in_scope = login(moderator).post("/products", payload(assigned), format="json")
    outside = login(moderator).post("/products", payload(other), format="json")
    admin = login(administrator).post("/products", payload(other), format="json")

    assert guest.status_code == 401
    assert user.status_code == 403
    assert in_scope.status_code == 201
    assert (outside.status_code, code(outside)) == (403, "CATEGORY_NOT_MANAGED")
    assert admin.status_code == 201
    assert Product.objects.count() == 2


def test_moderator_creates_in_assigned_subcategory(login, moderator):
    root = make("Dom")
    child = make("Organizery", root)
    assign(root, moderator)

    response = login(moderator).post("/products", payload(child), format="json")

    assert response.status_code == 201
    assert Product.objects.get().created_by == moderator


def test_patch_roles_and_scope(login, regular_user, moderator, administrator):
    assigned, other = make("Dom"), make("Figurki")
    assign(assigned, moderator)
    own = make_product(assigned)
    url = f"/products/{own.id}"

    assert APIClient().patch(url, {"name": "X"}, format="json").status_code == 401
    assert login(regular_user).patch(url, {"name": "X"}, format="json").status_code == 403
    assert login(moderator).patch(url, {"name": "Nowa"}, format="json").status_code == 200
    moved = login(moderator).patch(url, {"category_id": other.id}, format="json")
    assert (moved.status_code, code(moved)) == (403, "CATEGORY_NOT_MANAGED")
    assert (
        login(administrator).patch(url, {"category_id": other.id}, format="json").status_code == 200
    )


def test_patch_other_moderators_product(login, moderator):
    assigned, other = make("Dom"), make("Figurki")
    assign(assigned, moderator)
    published = make_product(other, published=True)
    draft = make_product(make("Prezenty"))
    client = login(moderator)

    # a published product is public, so refusing is fine; a draft's existence is not revealed
    response = client.patch(f"/products/{published.id}", {"name": "X"}, format="json")
    assert (response.status_code, code(response)) == (403, "CATEGORY_NOT_MANAGED")
    response = client.patch(f"/products/{draft.id}", {"name": "X"}, format="json")
    assert (response.status_code, code(response)) == (404, "PRODUCT_NOT_FOUND")
    assert set(Product.objects.values_list("name", flat=True)) == {"Istniejący"}


def test_patch_unknown_product_404(login, administrator):
    response = login(administrator).patch("/products/999999", {"name": "X"}, format="json")
    assert (response.status_code, code(response)) == (404, "PRODUCT_NOT_FOUND")


def test_no_delete_and_no_put(login, administrator):
    product = make_product(make("Dom"))
    client = login(administrator)

    assert client.delete(f"/products/{product.id}").status_code == 405
    assert client.put(f"/products/{product.id}", {"name": "X"}, format="json").status_code == 405


# --- description (stored XSS) ---


@pytest.mark.parametrize(
    ("description", "expected"),
    [
        ({"type": "doc", "content": [{"type": "script"}]}, "node_not_allowed"),
        (
            {"type": "doc", "content": [{"type": "image", "attrs": {"src": "x"}}]},
            "node_not_allowed",
        ),
        (
            {
                "type": "doc",
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": "klik",
                                "marks": [
                                    {"type": "link", "attrs": {"href": "javascript:alert(1)"}}
                                ],
                            }
                        ],
                    }
                ],
            },
            "link_not_allowed",
        ),
        ({"type": "doc", "content": [{"type": "paragraph", "onclick": "x()"}]}, "attr_not_allowed"),
        ("<script>alert(1)</script>", "invalid_document"),
        ({"type": "paragraph"}, "invalid_document"),
        ([], "invalid_document"),
    ],
)
def test_description_errors_as_field_codes(login, administrator, description, expected):
    body = payload(make("Dom"), description=description)

    response = login(administrator).post("/products", body, format="json")

    assert (response.status_code, code(response)) == (400, "VALIDATION_ERROR")
    assert {"field": "description", "type": expected} in field_errors(response)
    assert Product.objects.count() == 0


def test_valid_description_is_stored_unchanged(login, administrator):
    response = login(administrator).post(
        "/products", payload(make("Dom"), description=DESCRIPTION), format="json"
    )

    assert response.status_code == 201
    assert response.json()["description"] == DESCRIPTION
    assert Product.objects.get().description == DESCRIPTION


def test_patch_with_invalid_description_changes_nothing(login, administrator):
    product = make_product(make("Dom"))
    bad = {"type": "doc", "content": [{"type": "script"}]}

    response = login(administrator).patch(
        f"/products/{product.id}", {"name": "Zmieniona", "description": bad}, format="json"
    )

    assert response.status_code == 400
    product.refresh_from_db()
    assert product.name == "Istniejący" and product.description == DESCRIPTION


# --- field validation ---


@pytest.mark.parametrize("price", [0, "0", "0.00", -1, "-5.00", "abc", "", 12.345, "12.345", None])
def test_price_validation(login, administrator, price):
    body = payload(make("Dom"), variants=[variant(price=price)])

    response = login(administrator).post("/products", body, format="json")

    assert (response.status_code, code(response)) == (400, "VALIDATION_ERROR")
    assert Product.objects.count() == 0


def test_price_is_returned_as_text_with_two_places(login, administrator):
    body = payload(make("Dom"), variants=[variant(price=49), variant(size="L", price="49.5")])

    response = login(administrator).post("/products", body, format="json")

    assert response.status_code == 201
    assert [item["price"] for item in response.json()["variants"]] == ["49.00", "49.50"]
    assert response.json()["price_from"] == "49.00"


@pytest.mark.parametrize("stock", [-1, "abc", 1.5, None])
def test_invalid_stock_400(login, administrator, stock):
    body = payload(make("Dom"), variants=[variant(stock=stock)])

    response = login(administrator).post("/products", body, format="json")

    assert (response.status_code, code(response)) == (400, "VALIDATION_ERROR")


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"name": "", "category_id": 1},
        {"name": "   ", "category_id": 1},
        {"name": "x" * 201, "category_id": 1},
        {"name": "Figurka"},
        {"name": "Figurka", "category_id": "abc"},
        {"name": "Figurka", "category_id": 999_999},
        {"name": "Figurka", "category_id": 1, "is_published": "maybe"},
        {"name": "Figurka", "category_id": 1, "variants": "x"},
        {"name": "Figurka", "category_id": 1, "variants": [{"stock": 1}]},  # no price
    ],
)
def test_invalid_product_fields_400(login, administrator, body):
    if body.get("category_id") == 1:
        body = {**body, "category_id": make("Dom").id}

    response = login(administrator).post("/products", body, format="json")

    assert (response.status_code, code(response)) == (400, "VALIDATION_ERROR")
    assert Product.objects.count() == 0


def test_duplicate_variant_combination_400(login, administrator):
    body = payload(make("Dom"), variants=[variant(size="M"), variant(size="M")])

    response = login(administrator).post("/products", body, format="json")

    assert (response.status_code, code(response)) == (400, "VALIDATION_ERROR")
    assert {"field": "variants", "type": "duplicate_variant"} in field_errors(response)


def test_publish_rules_400(login, administrator):
    category = make("Dom")
    client = login(administrator)

    no_variant = client.post(
        "/products", payload(category, description=DESCRIPTION, is_published=True), format="json"
    )
    no_description = client.post(
        "/products", payload(category, is_published=True, variants=[variant()]), format="json"
    )

    assert (no_variant.status_code, code(no_variant)) == (400, "PUBLISH_REQUIRES_VARIANT")
    assert (no_description.status_code, code(no_description)) == (
        400,
        "PUBLISH_REQUIRES_DESCRIPTION",
    )
    assert Product.objects.count() == 0


# --- variants on PATCH ---


def test_patch_variants_replace(login, administrator):
    category = make("Dom")
    product = make_product(category, size="S")
    keep = product.variants.get()
    ProductVariant.objects.create(product=product, price=Decimal("20.00"), size="M")
    client = login(administrator)

    response = client.patch(
        f"/products/{product.id}",
        {"variants": [{"id": keep.id, "price": "15.00"}, variant(size="XL")]},
        format="json",
    )

    assert response.status_code == 200
    sizes = [(v["size"], v["price"]) for v in response.json()["variants"]]
    assert sizes == [("S", "15.00"), ("XL", "49.00")]
    assert product.variants.count() == 2  # the omitted "M" is gone


def test_patch_without_variants_keeps_them_and_empty_body_is_ok(login, administrator):
    product = make_product(make("Dom"))

    response = login(administrator).patch(f"/products/{product.id}", {}, format="json")

    assert response.status_code == 200
    assert product.variants.count() == 1


def test_new_variant_in_patch_still_needs_a_price(login, administrator):
    product = make_product(make("Dom"))

    response = login(administrator).patch(
        f"/products/{product.id}", {"variants": [{"color": "zielony"}]}, format="json"
    )

    assert (response.status_code, code(response)) == (400, "VALIDATION_ERROR")
    assert product.variants.count() == 1


def test_foreign_variant_id_400(login, administrator):
    product = make_product(make("Dom"))
    other = make_product(make("Figurki"))
    foreign = other.variants.get()

    response = login(administrator).patch(
        f"/products/{product.id}", {"variants": [{"id": foreign.id}]}, format="json"
    )

    assert (response.status_code, code(response)) == (400, "VARIANT_NOT_FOUND")


def test_publishing_through_patch(login, administrator):
    product = make_product(make("Dom"))

    response = login(administrator).patch(
        f"/products/{product.id}", {"is_published": True}, format="json"
    )

    assert response.status_code == 200 and response.json()["is_published"] is True


# --- response shape ---


def test_response_shape_detail(login, administrator):
    root = make("Dom")
    child = make("Organizery", root)
    body = payload(
        child,
        description=DESCRIPTION,
        is_published=True,
        variants=[variant(size="S", stock=0, made_to_order=True)],
    )

    response = login(administrator).post("/products", body, format="json")

    assert response.status_code == 201
    result = response.json()
    assert set(result) == {
        "id",
        "name",
        "description",
        "is_published",
        "category",
        "category_path",
        "price_from",
        "availability",
        "variants",
    }
    assert result["category"] == {"id": child.id, "name": "Organizery"}
    assert result["category_path"] == [
        {"id": root.id, "name": "Dom"},
        {"id": child.id, "name": "Organizery"},
    ]
    assert result["availability"] == "MADE_TO_ORDER"
    assert set(result["variants"][0]) == {
        "id",
        "color",
        "material",
        "size",
        "price",
        "stock",
        "made_to_order",
        "availability",
    }
    assert result["variants"][0]["availability"] == "MADE_TO_ORDER"
