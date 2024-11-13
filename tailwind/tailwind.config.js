/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    '../app/templates/app/**/*.{html,js}',
  ],
  theme: {
    extend: {},
  },
  plugins: [
    require('@tailwindcss/forms'),
  ],
  safelist: [
    'alert-info',
    'alert-success',
    'alert-warning',
    'alert-error',
  ],
}

