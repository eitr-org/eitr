let messages: Record<string, string> | undefined;
export function message(key: string, values: Record<string, string | number> = {}) {
  messages ??= JSON.parse(document.getElementById('site-messages')?.textContent ?? '{}');
  const text = messages![key];
  if (text === undefined) throw new Error(`Unknown website client message: ${key}`);
  return text.replace(/\{(\w+)\}/g, (placeholder, name: string) => String(values[name] ?? placeholder));
}
