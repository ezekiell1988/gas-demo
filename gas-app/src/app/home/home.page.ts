import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import {
  IonHeader,
  IonToolbar,
  IonTitle,
  IonContent,
  IonCard,
  IonCardHeader,
  IonCardTitle,
  IonCardContent,
  IonButton,
  IonIcon,
  IonBadge,
  IonItem,
  IonLabel,
  IonSpinner,
  IonGrid,
  IonRow,
  IonCol,
  IonList,
  IonNote,
} from '@ionic/angular/standalone';
import { addIcons } from 'ionicons';
import {
  checkmarkCircle,
  closeCircle,
  timeOutline,
  businessOutline,
  refreshOutline,
  logOutOutline,
  syncOutline,
  logInOutline,
} from 'ionicons/icons';

interface AuthStatus {
  authenticated: boolean;
  token_valid: boolean;
  realm_id: string | null;
  expires_at: string | null;
}

@Component({
  selector: 'app-home',
  templateUrl: 'home.page.html',
  imports: [
    CommonModule,
    IonHeader,
    IonToolbar,
    IonTitle,
    IonContent,
    IonCard,
    IonCardHeader,
    IonCardTitle,
    IonCardContent,
    IonButton,
    IonIcon,
    IonBadge,
    IonItem,
    IonLabel,
    IonSpinner,
    IonGrid,
    IonRow,
    IonCol,
    IonList,
    IonNote,
  ],
})
export class HomePage implements OnInit {
  authStatus: AuthStatus | null = null;
  loading = true;
  hasCookie = false;
  loggedOut = false;

  constructor(private http: HttpClient) {
    addIcons({
      checkmarkCircle,
      closeCircle,
      timeOutline,
      businessOutline,
      refreshOutline,
      logOutOutline,
      syncOutline,
      logInOutline,
    });
  }

  ngOnInit() {
    this.loadAuthInfo();
  }

  loadAuthInfo() {
    this.loading = true;

    this.http.get<AuthStatus>('/v1/auth/status').subscribe({
      next: (status) => {
        this.authStatus = status;
        this.checkCookie();
        this.loading = false;
        console.log('✅ Estado de autenticación:', status);
      },
      error: (err) => {
        console.error('❌ Error:', err);
        // Si hay error, el guard redirigirá al login
        this.loading = false;
      },
    });
  }

  checkCookie() {
    // Verificar si existe la cookie qb_session
    this.hasCookie = document.cookie
      .split(';')
      .some((c) => c.trim().startsWith('qb_session='));
    console.log('🍪 Cookie qb_session presente:', this.hasCookie);
  }

  refresh() {
    this.loadAuthInfo();
  }

  refreshToken() {
    this.loading = true;

    this.http.post('/v1/auth/refresh', {}).subscribe({
      next: (response: any) => {
        console.log('✅ Token renovado:', response);
        // Recargar información de autenticación
        this.loadAuthInfo();
      },
      error: (err) => {
        console.error('❌ Error renovando token:', err);
        this.loading = false;
        // Si falla, redirigir al login
        window.location.href = '/v1/auth/login';
      },
    });
  }

  logout() {
    this.loading = true;

    this.http.post('/v1/auth/logout', {}).subscribe({
      next: (response: any) => {
        console.log('✅ Sesión cerrada:', response);
        this.loading = false;
        this.loggedOut = true;
      },
      error: (err) => {
        console.error('❌ Error cerrando sesión:', err);
        // Aún así limpiar cookie y marcar como logged out
        document.cookie =
          'qb_session=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
        this.loading = false;
        this.loggedOut = true;
      },
    });
  }

  relogin() {
    // Recargar la página para que el guard redirija al login
    window.location.href = '/v1/auth/login';
  }

  getExpiresIn(): string {
    if (!this.authStatus?.expires_at) return 'N/A';

    const expiresAt = new Date(this.authStatus.expires_at);
    const now = new Date();
    const diff = expiresAt.getTime() - now.getTime();

    if (diff < 0) return 'Expirado';

    const minutes = Math.floor(diff / 60000);
    const seconds = Math.floor((diff % 60000) / 1000);

    return `${minutes}m ${seconds}s`;
  }
}
