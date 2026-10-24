import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { SignupInput, signup } from "../api";
import { useAuth } from "../auth";

const EMPTY: SignupInput = { first_name: "", last_name: "", email: "", password: "", confirm_password: "" };
const MIN_PASSWORD = 8;

export default function Signup() {
  const { user, setUser } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState<SignupInput>(EMPTY);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const update = (field: keyof SignupInput) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((f) => ({ ...f, [field]: e.target.value }));

  const mismatch = form.confirm_password.length > 0 && form.password !== form.confirm_password;

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (form.password.length < MIN_PASSWORD) return setError(`Password must be at least ${MIN_PASSWORD} characters.`);
    if (form.password !== form.confirm_password) return setError("Passwords do not match.");
    setBusy(true);
    try {
      setUser(await signup(form));
      navigate("/products");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  if (user) {
    return (
      <section className="page narrow">
        <h1>You're all set</h1>
        <p>You're logged in as {user.email}. <Link to="/products">Start shopping →</Link></p>
      </section>
    );
  }

  return (
    <section className="page narrow">
      <h1>Create account</h1>
      <p className="muted">Save your chats and keep track of the pieces you love.</p>
      <form className="form" onSubmit={onSubmit}>
        <div className="row">
          <label>
            First name
            <input value={form.first_name} onChange={update("first_name")} required autoComplete="given-name" />
          </label>
          <label>
            Last name
            <input value={form.last_name} onChange={update("last_name")} required autoComplete="family-name" />
          </label>
        </div>
        <label>
          Email
          <input type="email" value={form.email} onChange={update("email")} required autoComplete="email" />
        </label>
        <label>
          Password
          <input
            type="password"
            value={form.password}
            onChange={update("password")}
            required
            minLength={MIN_PASSWORD}
            autoComplete="new-password"
          />
          <small className="hint">At least {MIN_PASSWORD} characters.</small>
        </label>
        <label>
          Confirm password
          <input
            type="password"
            value={form.confirm_password}
            onChange={update("confirm_password")}
            required
            autoComplete="new-password"
            aria-invalid={mismatch}
          />
          {mismatch && <small className="hint bad">Passwords don't match yet.</small>}
        </label>
        {error && <p className="form-error" role="alert">{error}</p>}
        <button className="btn" type="submit" disabled={busy}>
          {busy ? "Creating account…" : "Create account"}
        </button>
      </form>
      <p className="muted">
        Already have an account? <Link to="/login">Log in</Link>
      </p>
    </section>
  );
}
