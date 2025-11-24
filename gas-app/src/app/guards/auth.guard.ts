import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { catchError, map, of, tap } from 'rxjs';
import { AuthService } from '../services/auth.service';

// Bandera para evitar múltiples redirects
let isRedirecting = false;

export const authGuard: CanActivateFn = (route, state) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  // Si ya estamos redirigiendo, no hacer nada más
  if (isRedirecting) {
    console.log('⏳ Ya hay un redirect en proceso, esperando...');
    return false;
  }

  // Verificar estado de autenticación directamente con el backend
  return authService.getAuthStatus().pipe(
    tap((status) => {
      console.log('📊 Estado recibido:', status);
    }),
    map((status) => {
      if (status.authenticated && status.token_valid) {
        console.log('✅ Usuario autenticado [Guard]');
        // Resetear bandera en caso de éxito
        isRedirecting = false;
        return true;
      } else {
        console.log('❌ No autenticado o token inválido, redirigiendo a login [Guard]');
        if (!isRedirecting) {
          isRedirecting = true;
          console.log('🔄 Iniciando redirect a /v1/auth/login');
          window.location.href = '/v1/auth/login';
        }
        return false;
      }
    }),
    catchError((error) => {
      console.error('❌ Error verificando autenticación [Guard]:', error);
      if (!isRedirecting) {
        isRedirecting = true;
        console.log('🔄 Error detectado, redirigiendo a /v1/auth/login');
        window.location.href = '/v1/auth/login';
      }
      return of(false);
    })
  );
};
