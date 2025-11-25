export interface Employee {
  Id?: string;
  SyncToken?: string;
  GivenName: string;
  FamilyName: string;
  MiddleName?: string;
  DisplayName?: string;
  Title?: string;
  Suffix?: string;
  PrimaryEmailAddr?: {
    Address?: string;
  };
  PrimaryPhone?: {
    FreeFormNumber?: string;
  };
  Mobile?: {
    FreeFormNumber?: string;
  };
  PrimaryAddr?: {
    Line1?: string;
    Line2?: string;
    City?: string;
    CountrySubDivisionCode?: string;
    PostalCode?: string;
  };
  EmployeeNumber?: string;
  SSN?: string;
  Gender?: string;
  HiredDate?: string;
  ReleasedDate?: string;
  BirthDate?: string;
  BillableTime?: boolean;
  BillRate?: number;
  CostRate?: number;
  Active?: boolean;
}

export interface EmployeeResponse {
  status: string;
  count?: number;
  employees?: Employee[];
  employee?: Employee;
  message?: string;
}
