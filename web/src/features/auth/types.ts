export type UserRole = "user" | "moderator" | "admin";

/** Roles an administrator can assign (administrators come from createsuperuser). */
export type ManagedRole = Exclude<UserRole, "admin">;

export type User = {
  id: number;
  email: string;
  username: string;
  first_name: string;
  last_name: string;
  role: UserRole;
  is_active: boolean;
  date_joined: string;
};

export type LoginInput = {
  login: string; // e-mail or username
  password: string;
};

export type RegisterInput = {
  email: string;
  username: string;
  first_name: string;
  last_name: string;
  password: string;
};
