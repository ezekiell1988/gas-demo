import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { HeaderComponent } from '../components';
import {
  IonContent,
  IonButton,
  IonIcon,
  IonBackButton,
  IonList,
  IonItem,
  IonLabel,
  IonInput,
  IonSpinner,
  IonSelect,
  IonSelectOption,
  ToastController
} from '@ionic/angular/standalone';
import { addIcons } from 'ionicons';
import { save, arrowBack } from 'ionicons/icons';
import { EmployeeService } from '../services';
import { Employee } from '../models';

@Component({
  selector: 'app-employee-detail',
  templateUrl: './employee-detail.page.html',
  standalone: true,
  imports: [
    ReactiveFormsModule,
    HeaderComponent,
    IonContent,
    IonButton,
    IonIcon,
    IonBackButton,
    IonList,
    IonItem,
    IonLabel,
    IonInput,
    IonSpinner,
    IonSelect,
    IonSelectOption
  ]
})
export class EmployeeDetailPage implements OnInit {
  private fb = inject(FormBuilder);
  private employeeService = inject(EmployeeService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private toastController = inject(ToastController);

  employeeForm: FormGroup;
  loading = false;
  saving = false;
  isEditMode = false;
  employeeId: string | null = null;
  currentEmployee: Employee | null = null;

  constructor() {
    addIcons({ save, arrowBack });

    this.employeeForm = this.fb.group({
      GivenName: ['', [Validators.required, Validators.maxLength(100)]],
      FamilyName: ['', [Validators.required, Validators.maxLength(100)]],
      MiddleName: ['', Validators.maxLength(100)],
      DisplayName: ['', Validators.maxLength(500)],
      Title: ['', Validators.maxLength(16)],
      Email: ['', [Validators.email]],
      Phone: ['', Validators.maxLength(20)],
      Mobile: ['', Validators.maxLength(20)],
      AddressLine1: ['', Validators.maxLength(500)],
      City: ['', Validators.maxLength(255)],
      State: ['', Validators.maxLength(255)],
      PostalCode: [''],
      EmployeeNumber: ['', Validators.maxLength(100)],
      Gender: [''],
      HiredDate: ['']
    });
  }

  ngOnInit() {
    this.employeeId = this.route.snapshot.paramMap.get('id');

    if (this.employeeId && this.employeeId !== 'new') {
      this.isEditMode = true;
      this.loadEmployee(this.employeeId);
    }
  }

  loadEmployee(id: string) {
    this.loading = true;

    this.employeeService.getEmployee(id).subscribe({
      next: (response) => {
        if (response.employee) {
          this.currentEmployee = response.employee;
          this.populateForm(response.employee);
        }
        this.loading = false;
      },
      error: (err) => {
        this.showToast('Error al cargar empleado', 'danger');
        this.loading = false;
        this.router.navigate(['/employees']);
      }
    });
  }

  populateForm(employee: Employee) {
    this.employeeForm.patchValue({
      GivenName: employee.GivenName,
      FamilyName: employee.FamilyName,
      MiddleName: employee.MiddleName || '',
      DisplayName: employee.DisplayName || '',
      Title: employee.Title || '',
      Email: employee.PrimaryEmailAddr?.Address || '',
      Phone: employee.PrimaryPhone?.FreeFormNumber || '',
      Mobile: employee.Mobile?.FreeFormNumber || '',
      AddressLine1: employee.PrimaryAddr?.Line1 || '',
      City: employee.PrimaryAddr?.City || '',
      State: employee.PrimaryAddr?.CountrySubDivisionCode || '',
      PostalCode: employee.PrimaryAddr?.PostalCode || '',
      EmployeeNumber: employee.EmployeeNumber || '',
      Gender: employee.Gender || '',
      HiredDate: employee.HiredDate || ''
    });
  }

  onSubmit() {
    if (this.employeeForm.invalid) {
      this.showToast('Por favor complete los campos requeridos', 'warning');
      return;
    }

    this.saving = true;
    const formValue = this.employeeForm.value;

    if (this.isEditMode && this.currentEmployee) {
      // Para actualizar, mantener todos los campos del empleado original
      // y solo sobrescribir los campos del formulario
      const employeeData: Employee = {
        ...this.currentEmployee, // Mantener todos los campos originales
        GivenName: formValue.GivenName,
        FamilyName: formValue.FamilyName,
        MiddleName: formValue.MiddleName || undefined,
        DisplayName: formValue.DisplayName || undefined,
        Title: formValue.Title || undefined,
        PrimaryEmailAddr: formValue.Email ? { Address: formValue.Email } : undefined,
        PrimaryPhone: formValue.Phone ? { FreeFormNumber: formValue.Phone } : undefined,
        Mobile: formValue.Mobile ? { FreeFormNumber: formValue.Mobile } : undefined,
        PrimaryAddr: formValue.AddressLine1 ? {
          Line1: formValue.AddressLine1,
          City: formValue.City || undefined,
          CountrySubDivisionCode: formValue.State || undefined,
          PostalCode: formValue.PostalCode || undefined
        } : undefined,
        EmployeeNumber: formValue.EmployeeNumber || undefined,
        Gender: formValue.Gender || undefined,
        HiredDate: formValue.HiredDate || undefined
      };

      this.employeeService.updateEmployee(this.employeeId!, employeeData).subscribe({
        next: (response) => {
          this.showToast('Empleado actualizado exitosamente', 'success');
          this.saving = false;
          this.router.navigate(['/employees'], {
            state: { updatedEmployee: response.employee }
          });
        },
        error: (err) => {
          console.error('Error al actualizar:', err);
          const errorMsg = err.error?.detail?.errors?.[0]?.message || err.error?.detail?.message || 'Error al actualizar empleado';
          this.showToast(errorMsg, 'danger');
          this.saving = false;
        }
      });
    } else {
      // Para crear, solo enviar los campos del formulario
      const employeeData: Employee = {
        GivenName: formValue.GivenName,
        FamilyName: formValue.FamilyName,
        MiddleName: formValue.MiddleName || undefined,
        DisplayName: formValue.DisplayName || undefined,
        Title: formValue.Title || undefined,
        PrimaryEmailAddr: formValue.Email ? { Address: formValue.Email } : undefined,
        PrimaryPhone: formValue.Phone ? { FreeFormNumber: formValue.Phone } : undefined,
        Mobile: formValue.Mobile ? { FreeFormNumber: formValue.Mobile } : undefined,
        PrimaryAddr: formValue.AddressLine1 ? {
          Line1: formValue.AddressLine1,
          City: formValue.City || undefined,
          CountrySubDivisionCode: formValue.State || undefined,
          PostalCode: formValue.PostalCode || undefined
        } : undefined,
        EmployeeNumber: formValue.EmployeeNumber || undefined,
        Gender: formValue.Gender || undefined,
        HiredDate: formValue.HiredDate || undefined,
        Active: true
      };

      this.employeeService.createEmployee(employeeData).subscribe({
        next: (response) => {
          this.showToast('Empleado creado exitosamente', 'success');
          this.saving = false;
          this.router.navigate(['/employees'], {
            state: { newEmployee: response.employee }
          });
        },
        error: (err) => {
          console.error('Error al crear:', err);
          const errorMsg = err.error?.detail?.errors?.[0]?.message || err.error?.detail?.message || 'Error al crear empleado';
          this.showToast(errorMsg, 'danger');
          this.saving = false;
        }
      });
    }
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

  goBack() {
    this.router.navigate(['/employees']);
  }
}
