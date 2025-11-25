import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  IonHeader,
  IonToolbar,
  IonTitle,
  IonButtons,
  IonButton,
  IonMenuButton,
  IonIcon
} from '@ionic/angular/standalone';
import { addIcons } from 'ionicons';
import { menuOutline, shieldCheckmarkOutline } from 'ionicons/icons';

@Component({
  selector: 'app-header',
  templateUrl: './header.component.html',
  standalone: true,
  imports: [
    CommonModule,
    IonHeader,
    IonToolbar,
    IonTitle,
    IonButtons,
    IonButton,
    IonMenuButton,
    IonIcon
  ]
})
export class HeaderComponent {
  @Input() title: string = 'QuickBooks';
  @Input() showMenuButton: boolean = true;
  @Input() color: string = 'primary';

  constructor() {
    addIcons({ menuOutline, shieldCheckmarkOutline });
  }
}
