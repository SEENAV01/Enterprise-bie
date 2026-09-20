import React from "react";

const events = [{"event_id": "a", "label": "Synthetic event A"}, {"event_id": "b", "label": "Synthetic event B"}];

export const Timeline_e0_5c88e7a2: React.FC = () => {
  return (
    <div role="img" aria-label={"Synthetic timeline compiler fixture"}
      style={{display: "flex", alignItems: "center", gap: 16}}>
      {events.map((event,index) => (
        <React.Fragment key={event.event_id}>
          <div style={{display: "grid", justifyItems: "center", gap: 6}}>
            <div style={{width: 12, height: 12, borderRadius: 999, background: "currentColor"}} />
            <span>{event.label}</span>
          </div>
          {index < events.length - 1 ? <div style={{height: 2, flex: 1, background: "currentColor"}} /> : null}
        </React.Fragment>
      ))}
    </div>
  );
};
