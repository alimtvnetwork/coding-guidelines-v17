import { SlideLayout } from "@/components/SlideLayout";
import { BulletList } from "@/components/BulletList";

export default function ClosingSlide() {
  return (
    <SlideLayout
      eyebrow="Recap"
      title="Apply one transformation per PR"
      subtitle="Small reviewable diffs beat heroic refactors. Pick one, ship it, move on."
      footer={
        <>
          <span>github.com/alimtvnetwork/coding-guidelines-v15</span>
          <span>Md. Alim Ul Karim · Riseup Asia LLC</span>
        </>
      }
    >
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "var(--space-5)" }}>
        <BulletList
          items={[
            "PascalCase everywhere",
            "Guard clauses, no nesting",
            "Booleans: Is / Has / Can",
            "AppError.wrap on catch",
            "Structured logger calls",
          ]}
        />
        <BulletList
          items={[
            "Enums kill magic strings",
            "8–15 line functions",
            "Max 2 operands per if",
            "Positively-named guards",
            "Caches invalidate on mutation",
          ]}
        />
      </div>
    </SlideLayout>
  );
}
