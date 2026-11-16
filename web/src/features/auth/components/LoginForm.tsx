"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useForm } from "react-hook-form";
import type { Path } from "react-hook-form";

import { ApiError } from "@/shared/api/client";
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

import { useLogin } from "../hooks";
import { safeNextPath, withNext } from "../redirect";
import type { LoginInput } from "../types";
import { loginPasswordRules, loginRules } from "../validation";

// The password is never remembered
const NOT_STORED: readonly Path<LoginInput>[] = ["password"];

function isCredentialsError(error: unknown): boolean {
  return error instanceof ApiError && error.code === "INVALID_CREDENTIALS";
}

export function LoginForm() {
  const next = safeNextPath(useSearchParams().get("next"));
  const loginMutation = useLogin();
  const form = useForm<LoginInput>({
    defaultValues: { login: "", password: "" },
  });
  const {
    register,
    handleSubmit,
    resetField,
    setFocus,
    formState: { errors },
  } = form;
  const { clear } = usePersistedFormFields("login", form, NOT_STORED);

  // On success GuestGuard redirects to ?next=, so nothing to navigate here
  const onSubmit = handleSubmit((data) =>
    loginMutation.mutate(data, {
      onSuccess: () => clear(),
      onError: (error) => {
        if (isCredentialsError(error)) {
          // The login stays, the password is cleared and focused for another try
          resetField("password");
          setFocus("password");
        }
      },
    }),
  );

  return (
    <Card>
      <CardHeader>
        <h1 className="text-xl font-semibold">Zaloguj się</h1>
        <CardDescription>
          Podaj e-mail lub nazwę użytkownika i hasło.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={onSubmit} noValidate>
          <FieldGroup>
            {loginMutation.isError && (
              <FormAlert
                title="Nie udało się zalogować"
                // After a wrong password the focus goes to the password field instead
                focusOnShow={!isCredentialsError(loginMutation.error)}
              >
                {errorMessage(loginMutation.error)}
              </FormAlert>
            )}
            <FormField
              label="E-mail lub nazwa użytkownika"
              error={errors.login?.message}
            >
              {(control) => (
                <Input
                  {...control}
                  autoComplete="username"
                  {...register("login", loginRules)}
                />
              )}
            </FormField>
            <FormField label="Hasło" error={errors.password?.message}>
              {(control) => (
                <PasswordInput
                  {...control}
                  autoComplete="current-password"
                  {...register("password", loginPasswordRules)}
                />
              )}
            </FormField>
            <Button
              type="submit"
              className="w-full"
              disabled={loginMutation.isPending}
            >
              {loginMutation.isPending && <Spinner data-icon="inline-start" />}
              {loginMutation.isPending ? "Logowanie..." : "Zaloguj się"}
            </Button>
          </FieldGroup>
        </form>
      </CardContent>
      <CardFooter className="justify-center">
        <p className="text-sm text-muted-foreground">
          Nie masz konta?{" "}
          <Link
            href={withNext("/register", next)}
            className="rounded-sm font-medium text-foreground underline underline-offset-4"
          >
            Załóż konto
          </Link>
        </p>
      </CardFooter>
    </Card>
  );
}
