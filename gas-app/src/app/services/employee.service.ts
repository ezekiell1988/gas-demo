import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Employee, EmployeeResponse } from '../models';

@Injectable({
  providedIn: 'root'
})
export class EmployeeService {
  private apiUrl = '/v1';

  constructor(private http: HttpClient) {}

  getEmployees(active?: boolean, limit: number = 100): Observable<EmployeeResponse> {
    let url = `${this.apiUrl}/employees?limit=${limit}`;
    if (active !== undefined) {
      url += `&active=${active}`;
    }
    return this.http.get<EmployeeResponse>(url, { withCredentials: true });
  }

  getEmployee(id: string): Observable<EmployeeResponse> {
    return this.http.get<EmployeeResponse>(`${this.apiUrl}/employees/${id}`, { withCredentials: true });
  }

  createEmployee(employee: Employee): Observable<EmployeeResponse> {
    return this.http.post<EmployeeResponse>(`${this.apiUrl}/employees`, employee, { withCredentials: true });
  }

  updateEmployee(id: string, employee: Employee): Observable<EmployeeResponse> {
    return this.http.put<EmployeeResponse>(`${this.apiUrl}/employees/${id}`, employee, { withCredentials: true });
  }

  deleteEmployee(id: string): Observable<EmployeeResponse> {
    return this.http.delete<EmployeeResponse>(`${this.apiUrl}/employees/${id}`, { withCredentials: true });
  }

  activateEmployee(id: string): Observable<EmployeeResponse> {
    return this.http.post<EmployeeResponse>(`${this.apiUrl}/employees/${id}/activate`, {}, { withCredentials: true });
  }
}
