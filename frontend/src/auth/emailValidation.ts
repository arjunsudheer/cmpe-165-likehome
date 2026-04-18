const LOCAL_PART_RE = /^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+$/;
const DOMAIN_LABEL_RE = /^[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?$/;
const TOP_LEVEL_DOMAIN_RE = /^[A-Za-z]{2,63}$/;

export function isValidEmailFormat(rawEmail: string): boolean {
  const email = rawEmail.trim();
  if (!email || email.length > 254 || /\s/.test(email)) return false;

  const parts = email.split("@");
  if (parts.length !== 2) return false;

  const [localPart, domain] = parts;
  if (!localPart || !domain || localPart.length > 64 || domain.length > 253) {
    return false;
  }

  if (
    localPart.startsWith(".")
    || localPart.endsWith(".")
    || localPart.includes("..")
    || !LOCAL_PART_RE.test(localPart)
  ) {
    return false;
  }

  if (domain.startsWith(".") || domain.endsWith(".") || domain.includes("..")) {
    return false;
  }

  const labels = domain.split(".");
  if (labels.length < 2) return false;

  const topLevelDomain = labels[labels.length - 1];
  if (!TOP_LEVEL_DOMAIN_RE.test(topLevelDomain)) return false;

  return labels.every((label) => DOMAIN_LABEL_RE.test(label));
}
