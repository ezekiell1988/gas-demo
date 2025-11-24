import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { catchError, map, of } from 'rxjs';

interface AuthStatus {
  authenticated: boolean;
  token_valid: boolean;
  realm_id: string | null;
  expires_at: string | null;
}

export const authGuard: CanActivateFn = (route, state) => {
  const http = inject(HttpClient);
  const router = inject(Router);

  // Verificar estado de autenticación con el backend
  return http.get<AuthStatus>('/v1/auth/status').pipe(
    map((status) => {
      if (status.authenticated && status.token_valid) {
        console.log('✅ Usuario autenticado');
        return true;
      } else {
        console.log('❌ Usuario no autenticado, redirigiendo a login');
        // Redirigir al login de QuickBooks
        window.location.href = '/v1/auth/login';
        return false;
      }
    }),
    catchError((error) => {
      console.error('❌ Error verificando autenticación:', error);
      // En caso de error, asumir que no está autenticado
      window.location.href = '/v1/auth/login';
      return of(false);
    })
  );
};
