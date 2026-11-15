"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import type { Path } from "react-hook-form";
import { toast } from "sonner";

import {
  firstNameRules,
  lastNameRules,
  usernameRules,
} from "@/features/auth/validation";
import type { User } from "@/features/auth/types";
import { applyServerErrors } from "@/shared/api/apply-server-errors";
import { errorMessage } from "@/shared/api/error-messages";
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

import { useUpdateProfile } from "../hooks";
import type { ProfileInput } from "../types";

const FIELDS: readonly Path<ProfileInput>[] = [
  "username",
  "first_name",
  "last_name",
];

function toInput(user: User): ProfileInput {
  return {
    username: user.username,
    first_name: user.first_name,
    last_name: user.last_name,
  };
}

export function ProfileForm({ user }: { user: User }) {
  const updateProfile = useUpdateProfile();
  const [generalError, setGeneralError] = useState<unknown>(null);
  const {
    register,
    handleSubmit,
    setError,
    reset,
    formState: { errors },
  } = useForm<ProfileInput>({ defaultValues: toInput(user) });

  const onSubmit = handleSubmit((data) => {
    setGeneralError(null);
    updateProfile.mutate(data, {
      onSuccess: (saved) => {
        // Show what the server saved (it trims spaces)
        reset(toInput(saved));
        toast.success("Zapisano dane konta.");
      },
      onError: (error) => {
        if (!applyServerErrors(error, setError, FIELDS)) {
          setGeneralError(error);
        }
      },
    });
  });

  return (
    <Card>
      <CardHeader>
        <h2 className="text-base font-medium">Dane konta</h2>
        <CardDescription>
          E-mail: {user.email} (nie można go zmienić).
        </CardDescription>
      </CardHeader>

      <CardContent>
        <form onSubmit={onSubmit} noValidate>
          <FieldGroup>
            {generalError !== null && (
              <FormAlert title="Nie udało się zapisać zmian">
                {errorMessage(generalError)}
              </FormAlert>
            )}
            <FormField
              label="Nazwa użytkownika"
              description="Publiczna nazwa w społeczności."
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
            <Button type="submit" disabled={updateProfile.isPending}>
              {updateProfile.isPending && <Spinner data-icon="inline-start" />}
              {updateProfile.isPending ? "Zapisywanie..." : "Zapisz zmiany"}
            </Button>
          </FieldGroup>
        </form>
      </CardContent>
    </Card>
  );
}
