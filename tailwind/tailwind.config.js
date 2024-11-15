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
    'bg-green-50',
    'bg-orange-50',
    'bg-red-50',
    'bg-blue-50',
    'text-green-600',
    'text-orange-600',
    'text-red-600',
    'text-blue-600',
    'text-green-700',
    'text-orange-700',
    'text-red-700',
    'text-blue-700',
    'ring-green-600/20',
    'ring-orange-600/20',
    'ring-red-600/20',
    'ring-blue-600/20',
  ],
}

