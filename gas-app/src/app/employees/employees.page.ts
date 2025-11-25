import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import {
  IonHeader,
  IonToolbar,
  IonTitle,
  IonContent,
  IonButton,
  IonIcon,
  IonFab,
  IonFabButton,
  IonCard,
  IonCardHeader,
  IonCardTitle,
  IonCardSubtitle,
  IonCardContent,
  IonList,
  IonItem,
  IonLabel,
  IonSpinner,
  AlertController,
  ToastController
} from '@ionic/angular/standalone';
import { addIcons } from 'ionicons';
import { add, create, trash, person, mail, call, location } from 'ionicons/icons';
import { EmployeeService } from '../services';
import { Employee } from '../models';

@Component({
  selector: 'app-employees',
  templateUrl: './employees.page.html',
  standalone: true,
  imports: [
    CommonModule,
    IonHeader,
    IonToolbar,
    IonTitle,
    IonContent,
    IonButton,
    IonIcon,
    IonFab,
    IonFabButton,
    IonCard,
    IonCardHeader,
    IonCardTitle,
    IonCardSubtitle,
    IonCardContent,
    IonList,
    IonItem,
    IonLabel,
    IonSpinner
  ]
})
export class EmployeesPage implements OnInit {
  employees: Employee[] = [];
  loading = false;
  error = '';

  constructor(
    private employeeService: EmployeeService,
    private router: Router,
    private alertController: AlertController,
    private toastController: ToastController
  ) {
    addIcons({ add, create, trash, person, mail, call, location });
  }

  ngOnInit() {
    this.loadEmployees();
  }

  loadEmployees() {
    this.loading = true;
    this.error = '';

    this.employeeService.getEmployees(true).subscribe({
      next: (response) => {
        this.employees = response.employees || [];
        this.loading = false;
      },
      error: (err) => {
        this.error = 'Error al cargar empleados';
        this.loading = false;
        this.showToast('Error al cargar empleados', 'danger');
      }
    });
  }

  goToAdd() {
    this.router.navigate(['/employee-detail/new']);
  }

  goToEdit(employee: Employee) {
    this.router.navigate(['/employee-detail', employee.Id]);
  }

  async confirmDelete(employee: Employee) {
    const alert = await this.alertController.create({
      header: 'Confirmar',
      message: `¿Está seguro de desactivar a ${employee.DisplayName || employee.GivenName + ' ' + employee.FamilyName}?`,
      buttons: [
        {
          text: 'Cancelar',
          role: 'cancel'
        },
        {
          text: 'Desactivar',
          role: 'confirm',
          handler: () => {
            this.deleteEmployee(employee.Id!);
          }
        }
      ]
    });

    await alert.present();
  }

  deleteEmployee(id: string) {
    this.employeeService.deleteEmployee(id).subscribe({
      next: (response) => {
        this.showToast('Empleado desactivado exitosamente', 'success');
        this.loadEmployees();
      },
      error: (err) => {
        this.showToast('Error al desactivar empleado', 'danger');
      }
    });
  }

  async showToast(message: string, color: string) {
    const toast = await this.toastController.create({
      message,
      duration: 2000,
      color,
      position: 'bottom'
    });
    await toast.present();
  }

  getEmployeeInitials(employee: Employee): string {
    const first = employee.GivenName?.charAt(0) || '';
    const last = employee.FamilyName?.charAt(0) || '';
    return (first + last).toUpperCase();
  }
}
