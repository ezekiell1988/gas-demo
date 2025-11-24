import { Routes } from '@angular/router';
import { authGuard } from './guards/auth.guard';

export const routes: Routes = [
  {
    path: 'home',
    loadComponent: () => import('./home/home.page').then((m) => m.HomePage),
    canActivate: [authGuard], // Proteger ruta con guard de autenticación
  },
  {
    path: '',
    redirectTo: 'home',
    pathMatch: 'full',
  },
];
