import authService from './services/authService'
import farmService from './services/farmService'
import outbreakService from './services/outbreakService'
import alertService from './services/alertService'

// Compatibility facade for components that import the shared api object.
// Services call apiClient directly, so this module does not create circular imports.
export const api = {
  login: (payload) => authService.login(payload),
  register: (payload) => authService.register(payload),
  current: () => authService.current(),
  farms: farmService,
  outbreaks: outbreakService,
  alerts: alertService,
}
export default { authService, farmService, outbreakService, alertService }
