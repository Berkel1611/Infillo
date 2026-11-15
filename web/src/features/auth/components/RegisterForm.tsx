"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import type { Path } from "react-hook-form";

import { applyServerErrors } from "@/shared/api/apply-server-errors";
import { errorMessage } from "@/shared/api/error-messages";
import { usePersistedFormFields } from "@/shared/hooks/use-persisted-form-fields";
import { Button } from "@/shared/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
} from "@/shared/ui/card";
import { FieldGroup } from "@/shared/ui/field";
import { FormAlert } from "@/shared/ui/form-alert";
import { FormField } from "@/shared/ui/form-field";
import { Input } from "@/shared/ui/input";
import { PasswordInput } from "@/shared/ui/password-input";
import { Spinner } from "@/shared/ui/spinner";

import { useRegister } from "../hooks";
import { safeNextPath, withNext } from "../redirect";
import type { RegisterInput } from "../types";
import {
  emailRules,
  firstNameRules,
  lastNameRules,
  newPasswordRules,
  usernameRules,
} from "../validation";

const FIELDS: readonly Path<RegisterInput>[] = [
  "email",
  "username",
  "first_name",
  "last_name",
  "password",
];
// The password is never remembered
const NOT_STORED: readonly Path<RegisterInput>[] = ["password"];

export function RegisterForm() {
  const next = safeNextPath(useSearchParams().get("next"));
  const registerMutation = useRegister();
  // An error that does not belong to any field (network, server error)
  const [generalError, setGeneralError] = useState<unknown>(null);
  const form = useForm<RegisterInput>({
    defaultValues: {
      email: "",
      username: "",
      first_name: "",
      last_name: "",
      password: "",
    },
  });
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors },
  } = form;
  const { clear } = usePersistedFormFields("register", form, NOT_STORED);

  // On success GuestGuard redirects to ?next=, so nothing to navigate here
  const onSubmit = handleSubmit((data) => {
    setGeneralError(null);
    registerMutation.mutate(data, {
      onSuccess: () => clear(),
      onError: (error) => {
        // Taken e-mail or username, weak password...: shown next to the field
        if (!applyServerErrors(error, setError, FIELDS)) {
          setGeneralError(error);
        }
      },
    });
  });

  return (
    <Card>
      <CardHeader>
        <h1 className="text-xl font-semibold">Załóż konto</h1>
        <CardDescription>To zajmie tylko chwilę.</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={onSubmit} noValidate>
          <FieldGroup>
            {generalError !== null && (
              <FormAlert title="Nie udało się założyć konta">
                {errorMessage(generalError)}
              </FormAlert>
            )}
            <FormField label="E-mail" error={errors.email?.message}>
              {(control) => (
                <Input
                  {...control}
                  type="email"
                  autoComplete="email"
                  {...register("email", emailRules)}
                />
              )}
            </FormField>
            <FormField
              label="Nazwa użytkownika"
              description="Publiczna nazwa w społeczności: 3–30 znaków, litery, cyfry i . + - _"
              error={errors.username?.message}
            >
              {(control) => (
                <Input
                  {...control}
                  autoComplete="username"
                  {...register("username", usernameRules)}
                />
              )}
            </FormField>
            <div className="grid gap-7 sm:grid-cols-2 sm:gap-4">
              <FormField label="Imię" error={errors.first_name?.message}>
                {(control) => (
                  <Input
                    {...control}
                    autoComplete="given-name"
                    {...register("first_name", firstNameRules)}
                  />
                )}
              </FormField>
              <FormField label="Nazwisko" error={errors.last_name?.message}>
                {(control) => (
                  <Input
                    {...control}
                    autoComplete="family-name"
                    {...register("last_name", lastNameRules)}
                  />
                )}
              </FormField>
            </div>
            <FormField
              label="Hasło"
              description="Co najmniej 8 znaków."
              error={errors.password?.message}
            >
              {(control) => (
                <PasswordInput
                  {...control}
                  autoComplete="new-password"
                  {...register("password", newPasswordRules)}
                />
              )}
            </FormField>
            <Button
              type="submit"
              className="w-full"
              disabled={registerMutation.isPending}
            >
              {registerMutation.isPending && (
                <Spinner data-icon="inline-start" />
              )}
              {registerMutation.isPending
                ? "Zakładanie konta..."
                : "Załóż konto"}
            </Button>
          </FieldGroup>
        </form>
      </CardContent>
      <CardFooter className="justify-center">
        <p className="text-sm text-muted-foreground">
          Masz już konto?{" "}
          <Link
            href={withNext("/login", next)}
            className="rounded-sm font-medium text-foreground underline underline-offset-4"
          >
            Zaloguj się
          </Link>
        </p>
      </CardFooter>
    </Card>
  );
}
