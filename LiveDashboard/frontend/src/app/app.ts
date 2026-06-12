import { ChangeDetectionStrategy, Component } from '@angular/core';
import { Dashboard } from './components/dashboard/dashboard';

@Component({
  selector: 'app-root',
  imports: [Dashboard],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: '<app-dashboard />',
})
export class App {}
