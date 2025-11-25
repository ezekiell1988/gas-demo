export interface AuthStatus {
  authenticated: boolean;
  token_valid: boolean;
  realm_id: string | null;
  expires_at: string | null;
}
