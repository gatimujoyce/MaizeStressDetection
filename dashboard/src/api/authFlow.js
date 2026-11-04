import { httpClient } from './httpClient'

// Sign-in safety calls: phone check at sign-up, forgot password, and changing a password.
export const requestRegisterCode = (phone) => httpClient.post('/auth/register/code', { phone })
export const requestPasswordResetCode = (phone) => httpClient.post('/auth/forgot-password', { phone })
export const resetPassword = ({ phone, code, newPassword }) =>
  httpClient.post('/auth/reset-password', { phone, code, new_password: newPassword })
export const changePassword = ({ currentPassword, newPassword }) =>
  httpClient.post('/auth/change-password', { current_password: currentPassword, new_password: newPassword })
