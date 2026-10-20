// Thunder for every lightning strike, with or without the music (sound.ts).
import { rumble, closeThunder } from './sound';
import { STRIKE, type StrikeDetail } from './motion';

document.addEventListener(STRIKE, (event) => {
  const { strength, sound } = (event as CustomEvent<StrikeDetail>).detail;
  // Sound travels slower than light, but a long wait feels disconnected.
  setTimeout(() => sound === 'close-thunder' ? void closeThunder(strength) : rumble(strength), 80 + Math.random() * 170);
});
