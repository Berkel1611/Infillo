/** What the user edits in the profile form (e-mail cannot be changed). */
export type ProfileInput = {
  username: string;
  first_name: string;
  last_name: string;
};

export type ShippingAddress = {
  street: string;
  postal_code: string;
  city: string;
  phone: string;
};
