import { GoogleLogin } from "@react-oauth/google";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

interface GoogleAuthResponse {
  access_token: string;
  user_id: number;
  email: string;
  name: string | null;
}

interface GoogleAuthButtonProps {
  onError: (message: string) => void;
  text?: "signin_with" | "signup_with" | "continue_with";
  width?: string;
}

export default function GoogleAuthButton({
  onError,
  text = "signin_with",
  width = "320",
}: GoogleAuthButtonProps) {
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSuccess = async (credentialResponse: { credential?: string }) => {
    if (!credentialResponse.credential) {
      onError("Google sign-in did not return a credential.");
      return;
    }

    onError("");

    try {
      // Exchange the Google credential for the app's own JWT session.
      const res = await fetch("/auth/google", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ credential: credentialResponse.credential }),
      });
      const data = (await res.json()) as Partial<GoogleAuthResponse> & { error?: string };

      if (!res.ok) {
        onError(data.error || "Google sign-in failed.");
        return;
      }

      login({
        token: data.access_token as string,
        userId: data.user_id as number,
        email: data.email as string,
        name: (data.name as string | null) ?? null,
      });
      navigate("/");
    } catch {
      onError("Network error — please try again.");
    }
  };

  return (
    <GoogleLogin
      onSuccess={handleSuccess}
      onError={() => onError("Google sign-in failed — please try again.")}
      text={text}
      shape="rectangular"
      width={width}
    />
  );
}
