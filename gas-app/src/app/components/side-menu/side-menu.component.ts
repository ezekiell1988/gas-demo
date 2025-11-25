import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import {
  IonMenu,
  IonHeader,
  IonToolbar,
  IonTitle,
  IonContent,
  IonList,
  IonItem,
  IonIcon,
  IonLabel,
  IonMenuToggle,
  IonBadge,
  IonChip,
  IonSpinner,
  IonNote,
  IonButton,
  IonButtons,
  MenuController
} from '@ionic/angular/standalone';
import { addIcons } from 'ionicons';
import {
  homeOutline,
  peopleOutline,
  logOutOutline,
  shieldCheckmarkOutline,
  checkmarkCircle,
  closeCircle,
  businessOutline,
  timeOutline,
  keyOutline,
  syncOutline,
  informationCircleOutline,
  refreshOutline
} from 'ionicons/icons';
import { AuthService } from '../../services';
import { AuthStatus } from '../../models';

@Component({
  selector: 'app-side-menu',
  templateUrl: './side-menu.component.html',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    IonMenu,
    IonHeader,
    IonToolbar,
    IonTitle,
    IonContent,
    IonList,
    IonItem,
    IonIcon,
    IonLabel,
    IonMenuToggle,
    IonBadge,
    IonChip,
    IonSpinner,
    IonNote,
    IonButton,
    IonButtons
  ]
})
export class SideMenuComponent implements OnInit {
  private authService = inject(AuthService);
  private menuCtrl = inject(MenuController);
  private http = inject(HttpClient);

  authStatus: AuthStatus | null = null;
  loading = true;
  currentTime: string = '';
  private timeInterval: any;
  private serverTimeOffset: number = 0; // Diferencia entre servidor y cliente en ms

  constructor() {
    addIcons({
      homeOutline,
      peopleOutline,
      logOutOutline,
      shieldCheckmarkOutline,
      checkmarkCircle,
      closeCircle,
      businessOutline,
      timeOutline,
      keyOutline,
      syncOutline,
      informationCircleOutline,
      refreshOutline
    });
  }

  ngOnInit() {
    this.loadAuthInfo();
    this.syncServerTime();
    this.timeInterval = setInterval(() => {
      this.updateTime();
    }, 1000);
  }

  ngOnDestroy() {
    if (this.timeInterval) {
      clearInterval(this.timeInterval);
    }
  }

  syncServerTime() {
    this.http.get<any>('/v1/health').subscribe({
      next: (response) => {
        if (response.timestamp) {
          const serverTime = new Date(response.timestamp).getTime();
          const clientTime = new Date().getTime();
          this.serverTimeOffset = serverTime - clientTime;
          this.updateTime();
        }
      },
      error: () => {
        // Sin offset si falla
        this.serverTimeOffset = 0;
        this.updateTime();
      }
    });
  }

  updateTime() {
    const now = new Date(new Date().getTime() + this.serverTimeOffset);
    this.currentTime = now.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: true
    });
  }

  loadAuthInfo() {
    this.loading = true;
    this.authService.getAuthStatus().subscribe({
      next: (status) => {
        this.authStatus = status;
        this.loading = false;
      },
      error: () => {
        this.loading = false;
      },
    });
  }

  refresh() {
    this.loading = true;
    this.syncServerTime(); // Re-sincronizar hora del servidor
    this.authService.getAuthStatus(true).subscribe({
      next: (status) => {
        this.authStatus = status;
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
      next: () => {
        this.loadAuthInfo();
      },
      error: () => {
        this.loading = false;
        window.location.href = '/v1/auth/login';
      },
    });
  }

  async logout() {
    this.loading = true;
    this.authService.logout().subscribe({
      next: () => {
        this.loading = false;
        this.menuCtrl.close();
        window.location.href = '/v1/auth/login';
      },
      error: () => {
        document.cookie = 'qb_session=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
        this.loading = false;
        this.menuCtrl.close();
        window.location.href = '/v1/auth/login';
      },
    });
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
