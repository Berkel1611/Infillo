export const streetRules = {
  validate: (value: string) =>
    value.trim().length > 0 || "Podaj ulicę i numer domu.",
  maxLength: { value: 200, message: "Adres może mieć najwyżej 200 znaków." },
};

export const postalCodeRules = {
  required: "Podaj kod pocztowy.",
  pattern: {
    value: /^\d{2}-\d{3}$/,
    message: "Podaj kod pocztowy w formacie 00-000.",
  },
};

export const cityRules = {
  validate: (value: string) => value.trim().length > 0 || "Podaj miejscowość.",
  maxLength: {
    value: 100,
    message: "Nazwa miejscowości może mieć najwyżej 100 znaków.",
  },
};

// Optional: an empty phone is fine
export const phoneRules = {
  pattern: {
    value: /^[\d +]*$/,
    message: "Telefon może zawierać tylko cyfry, spacje i znak +.",
  },
  maxLength: { value: 20, message: "Telefon może mieć najwyżej 20 znaków." },
};
