import { WebApp } from '../types';

declare global {
  interface Window {
    Telegram: {
      WebApp: WebApp;
    };
  }
}

export const initTelegramApp = () => {
  if (window.Telegram?.WebApp) {
    const tg = window.Telegram.WebApp;
    tg.ready();
    tg.expand();
    
    // Set header color to match app theme
    tg.setHeaderColor('#020617'); // slate-950
    tg.setBackgroundColor('#020617');
    
    return true;
  }
  return false;
};

export const getTelegramUser = () => {
  if (window.Telegram?.WebApp?.initDataUnsafe?.user) {
    return window.Telegram.WebApp.initDataUnsafe.user;
  }
  return null;
};

export const closeTelegramApp = () => {
  if (window.Telegram?.WebApp) {
    window.Telegram.WebApp.close();
  }
};
