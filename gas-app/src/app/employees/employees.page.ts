import { Component, OnInit, inject } from '@angular/core';
import { Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { HeaderComponent } from '../components';
import {
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
  IonNote,
  IonToggle,
  IonRefresher,
  IonRefresherContent,
  IonInfiniteScroll,
  IonInfiniteScrollContent,
  IonSkeletonText,
  IonSearchbar,
  IonSelect,
  IonSelectOption,
  AlertController,
  ToastController
} from '@ionic/angular/standalone';
import { addIcons } from 'ionicons';
import { add, create, trash, person, mail, call, location, eye, filter, checkmarkCircle, search, arrowUp, arrowDown } from 'ionicons/icons';
import { EmployeeService } from '../services';
import { Employee } from '../models';

@Component({
  selector: 'app-employees',
  templateUrl: './employees.page.html',
  standalone: true,
  imports: [
    FormsModule,
    HeaderComponent,
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
    IonNote,
    IonToggle,
    IonRefresher,
    IonRefresherContent,
    IonInfiniteScroll,
    IonInfiniteScrollContent,
    IonSkeletonText,
    IonSearchbar,
    IonSelect,
    IonSelectOption
  ]
})
export class EmployeesPage implements OnInit {
  private employeeService = inject(EmployeeService);
  private router = inject(Router);
  private alertController = inject(AlertController);
  private toastController = inject(ToastController);

  employees: Employee[] = [];
  loading = false;
  error = '';
  showActiveOnly = true;

  // Paginación
  pageSize = 5;
  currentOffset = 0;
  hasMore = true;

  // Búsqueda y ordenamiento
  searchTerm = '';
  orderBy: 'GivenName' | 'FamilyName' | 'DisplayName' | 'EmployeeNumber' = 'GivenName';
  orderDir: 'ASC' | 'DESC' = 'ASC';
  searchTimeout: any;

  constructor() {
    addIcons({filter,person,mail,call,location,create,trash,eye,add,checkmarkCircle,search,arrowUp,arrowDown});
  }

  isReadOnlyEmployee(id: string): boolean {
    return id === '54' || id === '55';
  }

  ngOnInit() {
    this.loadEmployees();

    // Verificar si hay un empleado nuevo o actualizado desde la navegación
    const navigation = this.router.getCurrentNavigation();
    const state = navigation?.extras?.state || history.state;

    if (state?.newEmployee) {
      // Agregar nuevo empleado
      setTimeout(() => {
        this.handleNewEmployee(state.newEmployee);
      }, 100);
    } else if (state?.updatedEmployee) {
      // Actualizar empleado existente
      setTimeout(() => {
        this.handleUpdatedEmployee(state.updatedEmployee);
      }, 100);
    }
  }

  handleNewEmployee(newEmployee: Employee) {
    // Agregar al inicio si cumple con el filtro activo
    if (!this.showActiveOnly || newEmployee.Active !== false) {
      this.employees.unshift(newEmployee);
      // Si tenemos más de pageSize, eliminar el último
      if (this.employees.length > this.pageSize) {
        this.employees.pop();
      }
    }
  }

  handleUpdatedEmployee(updatedEmployee: Employee) {
    // Actualizar en la lista visible
    const index = this.employees.findIndex(emp => emp.Id === updatedEmployee.Id);
    if (index !== -1) {
      this.employees[index] = updatedEmployee;
    }
  }

  onSearch() {
    // Debounce para evitar múltiples llamadas
    clearTimeout(this.searchTimeout);
    this.searchTimeout = setTimeout(() => {
      this.loadEmployees();
    }, 500);
  }

  onSort(field: 'GivenName' | 'FamilyName' | 'DisplayName' | 'EmployeeNumber') {
    if (this.orderBy === field) {
      this.orderDir = this.orderDir === 'ASC' ? 'DESC' : 'ASC';
    } else {
      this.orderBy = field;
      this.orderDir = 'ASC';
    }
    this.loadEmployees();
  }

  handleRefresh(event: any) {
    this.currentOffset = 0;
    this.employeeService.getEmployees(
      this.showActiveOnly,
      this.pageSize,
      this.currentOffset,
      this.searchTerm || undefined,
      this.orderBy,
      this.orderDir
    ).subscribe({
      next: (response) => {
        this.employees = response.employees || [];
        this.hasMore = this.employees.length === this.pageSize;
        event.target.complete();
        this.showToast('Lista actualizada', 'success');
      },
      error: (err) => {
        event.target.complete();
        this.showToast('Error al actualizar', 'danger');
      }
    });
  }

  loadMore(event: any) {
    this.currentOffset += this.pageSize;
    this.employeeService.getEmployees(
      this.showActiveOnly,
      this.pageSize,
      this.currentOffset,
      this.searchTerm || undefined,
      this.orderBy,
      this.orderDir
    ).subscribe({
      next: (response) => {
        const newEmployees = response.employees || [];
        this.employees = [...this.employees, ...newEmployees];
        this.hasMore = newEmployees.length === this.pageSize;
        event.target.complete();
      },
      error: (err) => {
        this.hasMore = false;
        event.target.complete();
      }
    });
  }

  loadEmployees() {
    this.loading = true;
    this.error = '';
    this.currentOffset = 0;

    this.employeeService.getEmployees(
      this.showActiveOnly,
      this.pageSize,
      this.currentOffset,
      this.searchTerm || undefined,
      this.orderBy,
      this.orderDir
    ).subscribe({
      next: (response) => {
        this.employees = response.employees || [];
        this.hasMore = this.employees.length === this.pageSize;
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

  async confirmActivate(employee: Employee) {
    const alert = await this.alertController.create({
      header: 'Confirmar',
      message: `¿Está seguro de reactivar a ${employee.DisplayName || employee.GivenName + ' ' + employee.FamilyName}?`,
      buttons: [
        {
          text: 'Cancelar',
          role: 'cancel'
        },
        {
          text: 'Reactivar',
          role: 'confirm',
          handler: () => {
            this.activateEmployee(employee.Id!);
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
        // Actualizar la lista localmente
        if (this.showActiveOnly) {
          // Si solo mostramos activos, remover el empleado
          this.employees = this.employees.filter(emp => emp.Id !== id);
          // Si quedan menos de pageSize, cargar más
          if (this.employees.length < this.pageSize && this.hasMore) {
            this.currentOffset = this.employees.length;
            this.employeeService.getEmployees(
              this.showActiveOnly,
              1,
              this.currentOffset,
              this.searchTerm || undefined,
              this.orderBy,
              this.orderDir
            ).subscribe({
              next: (response) => {
                const newEmployees = response.employees || [];
                if (newEmployees.length > 0) {
                  this.employees.push(newEmployees[0]);
                }
              }
            });
          }
        } else {
          // Si mostramos todos, actualizar el estado Active a false
          const employee = this.employees.find(emp => emp.Id === id);
          if (employee) {
            employee.Active = false;
          }
        }
      },
      error: (err) => {
        this.showToast('Error al desactivar empleado', 'danger');
      }
    });
  }

  activateEmployee(id: string) {
    this.employeeService.activateEmployee(id).subscribe({
      next: (response) => {
        this.showToast('Empleado reactivado exitosamente', 'success');
        // Actualizar la lista localmente
        if (this.showActiveOnly) {
          // Si solo mostramos activos, actualizar el estado a true
          const employee = this.employees.find(emp => emp.Id === id);
          if (employee) {
            employee.Active = true;
          }
        } else {
          // Si mostramos todos (inactivos), remover el empleado
          this.employees = this.employees.filter(emp => emp.Id !== id);
          // Si quedan menos de pageSize, cargar más
          if (this.employees.length < this.pageSize && this.hasMore) {
            this.currentOffset = this.employees.length;
            this.employeeService.getEmployees(
              this.showActiveOnly,
              1,
              this.currentOffset,
              this.searchTerm || undefined,
              this.orderBy,
              this.orderDir
            ).subscribe({
              next: (response) => {
                const newEmployees = response.employees || [];
                if (newEmployees.length > 0) {
                  this.employees.push(newEmployees[0]);
                }
              }
            });
          }
        }
      },
      error: (err) => {
        this.showToast('Error al reactivar empleado', 'danger');
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
