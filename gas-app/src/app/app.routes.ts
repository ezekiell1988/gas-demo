import { Routes } from '@angular/router';
import { authGuard } from './guards/auth.guard';

export const routes: Routes = [
  {
    path: 'home',
    loadComponent: () => import('./home/home.page').then((m) => m.HomePage),
    canActivate: [authGuard], // Proteger ruta con guard de autenticación
  },
  {
    path: 'employees',
    loadComponent: () => import('./employees/employees.page').then((m) => m.EmployeesPage),
    canActivate: [authGuard],
  },
  {
    path: 'employee-detail/:id',
    loadComponent: () => import('./employee-detail/employee-detail.page').then((m) => m.EmployeeDetailPage),
    canActivate: [authGuard],
  },
  {
    path: '',
    redirectTo: 'home',
    pathMatch: 'full',
  },
];
