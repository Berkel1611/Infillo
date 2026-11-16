"use client";

import { CloudAlertIcon } from "@hugeicons/core-free-icons";
import { useState } from "react";
import { useForm } from "react-hook-form";
import type { Path } from "react-hook-form";
import { toast } from "sonner";

import { applyServerErrors } from "@/shared/api/apply-server-errors";
import { errorMessage } from "@/shared/api/error-messages";
import { PageMessage, PageSpinner } from "@/shared/layout/page-states";
import { Button } from "@/shared/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
} from "@/shared/ui/card";
import { FieldGroup } from "@/shared/ui/field";
import { FormAlert } from "@/shared/ui/form-alert";
import { FormField } from "@/shared/ui/form-field";
import { Input } from "@/shared/ui/input";
import { Spinner } from "@/shared/ui/spinner";

import { useAddress, useSaveAddress } from "../hooks";
import type { ShippingAddress } from "../types";
import {
  cityRules,
  phoneRules,
  postalCodeRules,
  streetRules,
} from "../validation";

const FIELDS: readonly Path<ShippingAddress>[] = [
  "street",
  "postal_code",
  "city",
  "phone",
];

const EMPTY: ShippingAddress = {
  street: "",
  postal_code: "",
  city: "",
  phone: "",
};

function AddressFields({ address }: { address: ShippingAddress | null }) {
  const saveAddress = useSaveAddress();
  const [generalError, setGeneralError] = useState<unknown>(null);
  const {
    register,
    handleSubmit,
    setError,
    reset,
    formState: { errors },
  } = useForm<ShippingAddress>({ defaultValues: address ?? EMPTY });

  const onSubmit = handleSubmit((data) => {
    setGeneralError(null);
    saveAddress.mutate(data, {
      onSuccess: (saved) => {
        reset(saved);
        toast.success("Zapisano adres wysyłki.");
      },
      onError: (error) => {
        if (!applyServerErrors(error, setError, FIELDS)) {
          setGeneralError(error);
        }
      },
    });
  });

  return (
    <form onSubmit={onSubmit} noValidate>
      <FieldGroup>
        {generalError !== null && (
          <FormAlert title="Nie udało się zapisać adresu">
            {errorMessage(generalError)}
          </FormAlert>
        )}
        <FormField label="Ulica i numer" error={errors.street?.message}>
          {(control) => (
            <Input
              {...control}
              autoComplete="street-address"
              {...register("street", streetRules)}
            />
          )}
        </FormField>
        <div className="grid gap-7 sm:grid-cols-[10rem_1fr] sm:gap-4">
          <FormField
            label="Kod pocztowy"
            description="Format 00-000."
            error={errors.postal_code?.message}
          >
            {(control) => (
              <Input
                {...control}
                inputMode="numeric"
                autoComplete="postal-code"
                {...register("postal_code", postalCodeRules)}
              />
            )}
          </FormField>
          <FormField label="Miejscowość" error={errors.city?.message}>
            {(control) => (
              <Input
                {...control}
                autoComplete="address-level2"
                {...register("city", cityRules)}
              />
            )}
          </FormField>
        </div>
        <FormField
          label="Telefon (opcjonalnie)"
          description="Przydatny kurierowi."
          error={errors.phone?.message}
        >
          {(control) => (
            <Input
              {...control}
              type="tel"
              autoComplete="tel"
              {...register("phone", phoneRules)}
            />
          )}
        </FormField>
        <Button type="submit" disabled={saveAddress.isPending}>
          {saveAddress.isPending && <Spinner data-icon="inline-start" />}
          {saveAddress.isPending ? "Zapisywanie..." : "Zapisz adres"}
        </Button>
      </FieldGroup>
    </form>
  );
}

export function AddressForm() {
  const { data: address, isPending, isError, refetch } = useAddress();

  return (
    <Card>
      <CardHeader>
        <h2 className="text-base font-medium">Adres wysyłki</h2>
        <CardDescription>
          Dostawa tylko na terenie Polski. Odbiorcą jest osoba z danych konta.
        </CardDescription>
      </CardHeader>
      <CardContent>
        {isPending ? (
          <PageSpinner />
        ) : isError ? (
          <PageMessage
            icon={CloudAlertIcon}
            title="Nie udało się wczytać adresu"
            description="Sprawdź połączenie i spróbuj ponownie."
            action={<Button onClick={() => refetch()}>Spróbuj ponownie</Button>}
            heading="h2"
          />
        ) : (
          <AddressFields address={address} />
        )}
      </CardContent>
    </Card>
  );
}
