import { useState, useEffect } from "react";
import "./CreditCardForm.css";

export interface SavedCard {
  id: string;
  name: string;
  last4: string;
  expiry: string; // MM/YY
  brand: "visa" | "mastercard" | "amex" | "discover" | "generic";
}

interface Props {
  onCardSelected: (card: SavedCard) => void;
  onCardCleared: () => void;
}

const LS_KEY = "lh_saved_cards";

/** Luhn algorithm — returns true if number passes the check */
function luhnCheck(num: string): boolean {
  const digits = num.replace(/\D/g, "");
  let sum = 0;
  let shouldDouble = false;
  for (let i = digits.length - 1; i >= 0; i--) {
    let d = parseInt(digits[i], 10);
    if (shouldDouble) {
      d *= 2;
      if (d > 9) d -= 9;
    }
    sum += d;
    shouldDouble = !shouldDouble;
  }
  return sum % 10 === 0;
}

/** Detect card brand from first digits */
function detectBrand(num: string): SavedCard["brand"] {
  const n = num.replace(/\D/g, "");
  if (/^4/.test(n)) return "visa";
  if (/^5[1-5]|^2[2-7]/.test(n)) return "mastercard";
  if (/^3[47]/.test(n)) return "amex";
  if (/^6(?:011|5)/.test(n)) return "discover";
  return "generic";
}

/** Format card number with spaces: 4444 4444 4444 4444 */
function formatCardNumber(raw: string): string {
  const digits = raw.replace(/\D/g, "").slice(0, 16);
  return digits.replace(/(.{4})/g, "$1 ").trim();
}

/** Format expiry as MM/YY */
function formatExpiry(raw: string): string {
  const digits = raw.replace(/\D/g, "").slice(0, 4);
  if (digits.length > 2) return digits.slice(0, 2) + "/" + digits.slice(2);
  return digits;
}

function loadCards(): SavedCard[] {
  try { return JSON.parse(localStorage.getItem(LS_KEY) ?? "[]"); }
  catch { return []; }
}

function saveCards(cards: SavedCard[]) {
  localStorage.setItem(LS_KEY, JSON.stringify(cards));
}

function brandLabel(brand: SavedCard["brand"]): string {
  return { visa: "Visa", mastercard: "Mastercard", amex: "Amex", discover: "Discover", generic: "Card" }[brand];
}

function brandIcon(brand: SavedCard["brand"]): string {
  return { visa: "💳", mastercard: "💳", amex: "💳", discover: "💳", generic: "💳" }[brand];
}

export default function CreditCardForm({ onCardSelected, onCardCleared }: Props) {
  const [savedCards, setSavedCards] = useState<SavedCard[]>(loadCards);
  const [selectedId, setSelectedId] = useState<string | null>(() => {
    const cards = loadCards();
    return cards.length > 0 ? cards[0].id : null;
  });
  const [showForm, setShowForm] = useState(false);

  // form fields
  const [cardNameField, setCardNameField] = useState("");
  const [cardNumberField, setCardNumberField] = useState("");
  const [cardExpiryField, setCardExpiryField] = useState("");
  const [cardCvvField, setCardCvvField] = useState("");
  const [flipped, setFlipped] = useState(false);

  // validation errors
  const [errs, setErrs] = useState<Record<string, string>>({});

  // Notify parent when selection changes
  useEffect(() => {
    if (selectedId) {
      const card = savedCards.find((c) => c.id === selectedId);
      if (card) onCardSelected(card);
    } else {
      onCardCleared();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedId, savedCards]);

  const brand = detectBrand(cardNumberField);
  const displayNumber = cardNumberField || "•••• •••• •••• ••••";
  const displayExpiry = cardExpiryField || "MM/YY";
  const displayName = cardNameField || "CARDHOLDER NAME";

  const validate = (): boolean => {
    const e: Record<string, string> = {};
    if (!cardNameField.trim()) e.name = "Cardholder name is required";
    const rawNum = cardNumberField.replace(/\D/g, "");
    if (rawNum.length < 16) {
      e.number = "Card number must be 16 digits";
    } else if (!luhnCheck(rawNum)) {
      e.number = "Invalid card number — please check and try again";
    }
    const expiryDigits = cardExpiryField.replace(/\D/g, "");
    if (expiryDigits.length < 4) {
      e.expiry = "Enter expiry as MM/YY";
    } else {
      const month = parseInt(expiryDigits.slice(0, 2), 10);
      const year = parseInt("20" + expiryDigits.slice(2, 4), 10);
      const now = new Date();
      const exp = new Date(year, month - 1, 1);
      if (month < 1 || month > 12) e.expiry = "Invalid month";
      else if (exp < new Date(now.getFullYear(), now.getMonth(), 1)) e.expiry = "Card is expired";
    }
    if (cardCvvField.length < 3) e.cvv = "Enter 3–4 digit CVV";
    setErrs(e);
    return Object.keys(e).length === 0;
  };

  const handleAddCard = () => {
    if (!validate()) return;
    const rawNum = cardNumberField.replace(/\D/g, "");
    const newCard: SavedCard = {
      id: Date.now().toString(),
      name: cardNameField.trim(),
      last4: rawNum.slice(-4),
      expiry: cardExpiryField,
      brand: detectBrand(rawNum),
    };
    const updated = [...savedCards, newCard];
    saveCards(updated);
    setSavedCards(updated);
    setSelectedId(newCard.id);
    setShowForm(false);
    // Reset
    setCardNameField("");
    setCardNumberField("");
    setCardExpiryField("");
    setCardCvvField("");
    setErrs({});
  };

  const handleRemoveCard = (id: string) => {
    const updated = savedCards.filter((c) => c.id !== id);
    saveCards(updated);
    setSavedCards(updated);
    if (selectedId === id) {
      const next = updated[0] ?? null;
      setSelectedId(next?.id ?? null);
      if (!next) onCardCleared();
    }
  };

  const handleSelect = (id: string) => {
    setSelectedId(id);
    const card = savedCards.find((c) => c.id === id)!;
    onCardSelected(card);
    setShowForm(false);
  };

  return (
    <div className="cc-form">
      {/* Saved cards */}
      {savedCards.length > 0 && !showForm && (
        <div className="cc-saved-list">
          {savedCards.map((card) => (
            <div
              key={card.id}
              className={`cc-saved-item${selectedId === card.id ? " selected" : ""}`}
              onClick={() => handleSelect(card.id)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => e.key === "Enter" && handleSelect(card.id)}
            >
              <div className="cc-saved-radio">
                <div className={`cc-radio-dot${selectedId === card.id ? " active" : ""}`} />
              </div>
              <div className="cc-saved-icon">{brandIcon(card.brand)}</div>
              <div className="cc-saved-info">
                <span className="cc-saved-brand">{brandLabel(card.brand)} ••••{card.last4}</span>
                <span className="cc-saved-expires">Expires {card.expiry} · {card.name}</span>
              </div>
              <button
                className="cc-remove-btn"
                onClick={(e) => { e.stopPropagation(); handleRemoveCard(card.id); }}
                title="Remove card"
                aria-label="Remove card"
              >
                ×
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Add new card toggle */}
      {!showForm ? (
        <button
          className="cc-add-btn"
          onClick={() => setShowForm(true)}
        >
          + Add new card
        </button>
      ) : (
        <div className="cc-add-panel">
          {/* Visual card preview */}
          <div
            className={`cc-card-preview${flipped ? " flipped" : ""}`}
            onClick={() => setFlipped((f) => !f)}
            title="Click to flip"
          >
            <div className="cc-card-inner">
              {/* Front */}
              <div className={`cc-card-face cc-card-front cc-brand-${brand}`}>
                <div className="cc-card-chip">▪</div>
                <div className="cc-card-number">{displayNumber}</div>
                <div className="cc-card-bottom">
                  <div>
                    <div className="cc-card-label">Cardholder</div>
                    <div className="cc-card-holder">{displayName.toUpperCase()}</div>
                  </div>
                  <div>
                    <div className="cc-card-label">Expires</div>
                    <div className="cc-card-expiry">{displayExpiry}</div>
                  </div>
                  <div className="cc-card-brand-text">{brandLabel(brand)}</div>
                </div>
              </div>
              {/* Back */}
              <div className="cc-card-face cc-card-back">
                <div className="cc-card-magstripe" />
                <div className="cc-card-sig-strip">
                  <span className="cc-cvv-label">CVV</span>
                  <span className="cc-cvv-val">{cardCvvField || "•••"}</span>
                </div>
                <div className="cc-card-back-note">Click to view front</div>
              </div>
            </div>
          </div>

          {/* Input fields */}
          <div className="cc-fields">
            <div className="form-group">
              <label className="form-label" htmlFor="cc-name">Cardholder name</label>
              <input
                id="cc-name"
                className={`form-input${errs.name ? " error" : ""}`}
                type="text"
                placeholder="Jane Smith"
                value={cardNameField}
                onChange={(e) => setCardNameField(e.target.value)}
                autoComplete="cc-name"
              />
              {errs.name && <span className="form-error">{errs.name}</span>}
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="cc-number">Card number</label>
              <input
                id="cc-number"
                className={`form-input cc-number-input${errs.number ? " error" : ""}`}
                type="text"
                inputMode="numeric"
                placeholder="1234 5678 9012 3456"
                value={cardNumberField}
                onChange={(e) => setCardNumberField(formatCardNumber(e.target.value))}
                autoComplete="cc-number"
                maxLength={19}
              />
              {errs.number && <span className="form-error">{errs.number}</span>}
            </div>

            <div className="cc-row-2">
              <div className="form-group">
                <label className="form-label" htmlFor="cc-expiry">Expiry (MM/YY)</label>
                <input
                  id="cc-expiry"
                  className={`form-input${errs.expiry ? " error" : ""}`}
                  type="text"
                  inputMode="numeric"
                  placeholder="MM/YY"
                  value={cardExpiryField}
                  onChange={(e) => setCardExpiryField(formatExpiry(e.target.value))}
                  autoComplete="cc-exp"
                  maxLength={5}
                />
                {errs.expiry && <span className="form-error">{errs.expiry}</span>}
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="cc-cvv">CVV</label>
                <input
                  id="cc-cvv"
                  className={`form-input${errs.cvv ? " error" : ""}`}
                  type="text"
                  inputMode="numeric"
                  placeholder="•••"
                  value={cardCvvField}
                  onChange={(e) => setCardCvvField(e.target.value.replace(/\D/g, "").slice(0, 4))}
                  autoComplete="cc-csc"
                  maxLength={4}
                  onFocus={() => setFlipped(true)}
                  onBlur={() => setFlipped(false)}
                />
                {errs.cvv && <span className="form-error">{errs.cvv}</span>}
              </div>
            </div>

            <div className="cc-form-actions">
              <button className="btn btn-secondary" onClick={() => { setShowForm(false); setErrs({}); }}>
                Cancel
              </button>
              <button className="btn btn-primary" onClick={handleAddCard}>
                Save Card
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
