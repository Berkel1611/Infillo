// Letters (also Polish), digits and . + - _ : same as the server rule, which cannot be
// written as a regex literal here because the tsconfig target is ES2017
const USERNAME_PATTERN = new RegExp("^[\\p{L}\\p{N}_.+-]+$", "u");
// Surrounding spaces are allowed: the server trims them
const EMAIL_PATTERN = /^\s*[^\s@]+@[^\s@]+\.[^\s@]+\s*$/;

export const loginRules = {
  validate: (value: string) =>
    value.trim().length > 0 || "Podaj e-mail lub nazwę użytkownika.",
};

export const loginPasswordRules = {
  required: "Podaj hasło.",
};

export const emailRules = {
  required: "Podaj adres e-mail.",
  pattern: {
    value: EMAIL_PATTERN,
    message: "Podaj poprawny adres e-mail, np. jan@przyklad.pl.",
  },
  maxLength: { value: 254, message: "Adres e-mail jest za długi." },
};

export const usernameRules = {
  required: "Podaj nazwę użytkownika.",
  minLength: {
    value: 3,
    message: "Nazwa użytkownika musi mieć co najmniej 3 znaki.",
  },
  maxLength: {
    value: 30,
    message: "Nazwa użytkownika może mieć najwyżej 30 znaków.",
  },
  pattern: {
    value: USERNAME_PATTERN,
    message:
      "Nazwa użytkownika może zawierać tylko litery, cyfry oraz znaki . + - _",
  },
};

export const firstNameRules = {
  validate: (value: string) => value.trim().length > 0 || "Podaj swoje imię.",
  maxLength: { value: 50, message: "Imię może mieć najwyżej 50 znaków." },
};

export const lastNameRules = {
  validate: (value: string) =>
    value.trim().length > 0 || "Podaj swoje nazwisko.",
  maxLength: { value: 80, message: "Nazwisko może mieć najwyżej 80 znaków." },
};

export const newPasswordRules = {
  required: "Podaj hasło.",
  minLength: { value: 8, message: "Hasło musi mieć co najmniej 8 znaków." },
  maxLength: { value: 128, message: "Hasło może mieć najwyżej 128 znaków." },
};
