// src/plugins/vuetify.ts
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'

export default createVuetify({
  components,
  directives,
  theme: {
    defaultTheme: 'platemateLight',
    themes: {
      platemateLight: {
        dark: false,
        colors: {
          primary: '#4caf50',
          secondary: '#ff7043',
          accent: '#82b1ff',
          info: '#2196f3',
        },
      },
    },
  },
})
