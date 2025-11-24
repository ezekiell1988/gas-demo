import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  IonHeader,
  IonToolbar,
  IonTitle,
  IonContent,
  IonCard,
  IonCardHeader,
  IonCardTitle,
  IonCardContent,
  IonCardSubtitle,
  IonButton,
  IonButtons,
  IonIcon,
  IonBadge,
  IonChip,
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
  shieldCheckmarkOutline,
  shieldCheckmark,
  shieldOutline,
  key,
  keyOutline,
  informationCircleOutline,
  hourglassOutline,
  lockClosedOutline,
  checkmark,
  close,
} from 'ionicons/icons';
import { AuthService, AuthStatus } from '../services/auth.service';

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
    IonCardSubtitle,
    IonButton,
    IonButtons,
    IonIcon,
    IonBadge,
    IonChip,
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

  constructor(private authService: AuthService) {
    addIcons({
      checkmarkCircle,
      closeCircle,
      timeOutline,
      businessOutline,
      refreshOutline,
      logOutOutline,
      syncOutline,
      logInOutline,
      shieldCheckmarkOutline,
      shieldCheckmark,
      shieldOutline,
      key,
      keyOutline,
      informationCircleOutline,
      hourglassOutline,
      lockClosedOutline,
      checkmark,
      close,
    });
  }

  ngOnInit() {
    this.loadAuthInfo();
  }

  loadAuthInfo() {
    this.loading = true;

    // Usar el servicio de autenticación (ya tiene caché del guard)
    this.authService.getAuthStatus().subscribe({
      next: (status) => {
        this.authStatus = status;
        this.checkCookie();
        this.loading = false;
        console.log('✅ Estado de autenticación [HomePage]:', status);
      },
      error: (err) => {
        console.error('❌ Error [HomePage]:', err);
        // Si hay error, el guard redirigirá al login
        this.loading = false;
      },
    });
  }

  checkCookie() {
    this.hasCookie = this.authService.hasCookie();
    console.log('🍪 Cookie qb_session presente:', this.hasCookie);
  }

  refresh() {
    // Forzar actualización del estado
    this.loading = true;
    this.authService.getAuthStatus(true).subscribe({
      next: (status) => {
        this.authStatus = status;
        this.checkCookie();
        this.loading = false;
      },
      error: () => {
        this.loading = false;
      },
    });
  }

  refreshToken() {
    this.loading = true;

    this.authService.refreshToken().subscribe({
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

    this.authService.logout().subscribe({
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

  getCurrentTime(): string {
    return new Date().toLocaleTimeString('es-ES', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  }
}
