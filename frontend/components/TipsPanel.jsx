"use client";

function PrePracticeBlock({ plan }) {
  if (!plan) return null;
  return (
    <div className="pre-practice-box">
      <div className="pre-practice-title">
        Before you come back here, try: <strong>{plan.activity_name}</strong>
      </div>
      <div className="pre-practice-meta">
        {plan.duration_per_session} · {plan.recommended_frequency}
      </div>
      <div className="pre-practice-section">
        <span className="pre-practice-label">How to practice:</span>
        <ul>{plan.how_to.map((step, i) => <li key={i}>{step}</li>)}</ul>
      </div>
      <div className="pre-practice-section">
        <span className="pre-practice-label">Real-world practice:</span>
        <ul>{plan.real_world_practice.map((item, i) => <li key={i}>{item}</li>)}</ul>
      </div>
    </div>
  );
}

function TipCategory({ title, data }) {
  if (!data) return null;
  return (
    <div className="tip-category">
      <h4 className="tip-headline">{title}: {data.headline}</h4>
      <ul className="tip-list">{data.tips.map((tip, i) => <li key={i}>{tip}</li>)}</ul>
      <PrePracticeBlock plan={data.pre_practice} />
    </div>
  );
}

export default function TipsPanel({ tips }) {
  if (!tips) return null;

  return (
    <div className="tips-wrapper">
      <h3>Tips to improve</h3>
      <TipCategory title="Content" data={tips.content} />
      <TipCategory title="Fluency" data={tips.fluency} />
      <TipCategory title="Pronunciation" data={tips.pronunciation} />
      {tips.general && tips.general.length > 0 && (
        <div className="tip-category general">
          <h4 className="tip-headline">Key strategy reminders</h4>
          <ul className="tip-list">{tips.general.map((tip, i) => <li key={i}>{tip}</li>)}</ul>
        </div>
      )}
    </div>
  );
}
