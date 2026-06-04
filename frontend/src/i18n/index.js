import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import bn from './bn.json';
import en from './en.json';
import hi from './hi.json';
import ar from './ar.json';

i18n
  .use(initReactI18next)
  .init({
    resources: {
      bn: { translation: bn },
      en: { translation: en },
      hi: { translation: hi },
      ar: { translation: ar },
    },
    lng: localStorage.getItem('dms-lang') || 'bn',
    fallbackLng: 'en',
    interpolation: { escapeValue: false },
  });

export default i18n;
