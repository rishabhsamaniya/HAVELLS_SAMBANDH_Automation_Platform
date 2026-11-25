import React from "react";
import logoImg from "@/assets/havells-sambandh-logo.png";

interface BrandLogoProps {
  size?: "sm" | "lg";
  subtitle?: string;
  centered?: boolean;
}

export const BrandLogo: React.FC<BrandLogoProps> = ({
  size = "lg",
  subtitle,
  centered = false,
}) => {
  const heightClass = size === "lg" ? "h-16 sm:h-20" : "h-11";
  return (
    <div className={`inline-flex flex-col ${centered ? "items-center text-center" : "items-start"}`}>
      <img
        src={logoImg}
        alt="HAVELLS Sambandh — Moving Forward, Together."
        className={`${heightClass} w-auto object-contain select-none`}
      />
      {subtitle && <span className="text-xs text-ink-secondary mt-1.5 font-medium">{subtitle}</span>}
    </div>
  );
};
