import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable, of } from 'rxjs';
import { tap, catchError, shareReplay } from 'rxjs/operators';
import { AuthStatus } from '../models';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private authStatusSubject = new BehaviorSubject<AuthStatus | null>(null);
  private authStatusCache$: Observable<AuthStatus> | null = null;

  // Observable público para que los componentes se suscriban
  public authStatus$ = this.authStatusSubject.asObservable();

  constructor(private http: HttpClient) {}

  /**
   * Obtiene el estado de autenticación del backend.
   * Usa caché para evitar llamadas HTTP duplicadas.
   */
  getAuthStatus(forceRefresh: boolean = false): Observable<AuthStatus> {
    // Si se solicita refresh o no hay caché, hacer nueva petición
    if (forceRefresh || !this.authStatusCache$) {
      console.log('🔄 Obteniendo estado de autenticación...');

      this.authStatusCache$ = this.http.get<AuthStatus>('/v1/auth/status').pipe(
        tap((status) => {
          console.log('✅ Estado de autenticación obtenido:', status);
          this.authStatusSubject.next(status);
        }),
        catchError((error) => {
          console.error('❌ Error obteniendo estado de autenticación:', error);
          this.authStatusSubject.next(null);
          throw error;
        }),
        shareReplay(1) // Compartir resultado entre suscriptores
      );
    }

    return this.authStatusCache$;
  }

  /**
   * Obtiene el valor actual del estado sin hacer una nueva petición HTTP
   */
  getCurrentAuthStatus(): AuthStatus | null {
    return this.authStatusSubject.value;
  }

  /**
   * Refresca el token de acceso
   */
  refreshToken(): Observable<any> {
    console.log('🔄 Renovando token...');

    return this.http.post('/v1/auth/refresh', {}).pipe(
      tap(() => {
        // Limpiar caché para forzar nueva consulta
        this.authStatusCache$ = null;
        // Obtener nuevo estado después del refresh
        this.getAuthStatus(true).subscribe();
      })
    );
  }

  /**
   * Cierra la sesión del usuario
   */
  logout(): Observable<any> {
    console.log('👋 Cerrando sesión...');

    return this.http.post('/v1/auth/logout', {}).pipe(
      tap(() => {
        // Limpiar estado
        this.authStatusSubject.next(null);
        this.authStatusCache$ = null;
      })
    );
  }

  /**
   * Limpia el caché del estado de autenticación
   */
  clearCache(): void {
    this.authStatusCache$ = null;
    this.authStatusSubject.next(null);
  }

  /**
   * Verifica si la cookie qb_session está presente.
   * NOTA: La cookie es HttpOnly, por lo que JavaScript no puede leerla directamente.
   * En su lugar, verificamos si el usuario está autenticado según el backend.
   * Si authenticated=true, significa que la cookie está presente y válida.
   */
  hasCookie(): boolean {
    const currentStatus = this.authStatusSubject.value;
    // Si el backend dice que estamos autenticados, la cookie HttpOnly está presente
    return currentStatus?.authenticated === true;
  }
}
