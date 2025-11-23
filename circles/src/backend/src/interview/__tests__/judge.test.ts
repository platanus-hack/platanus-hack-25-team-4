import { describe, it, expect } from "vitest";

import { MockInterviewJudge } from "../judge.js";
import type { JudgeInput } from "../types.js";

const baseInput: Omit<JudgeInput, "transcript"> = {
  owner_objective: "Conectar con otras personas para posibles colaboraciones.",
};

describe("MockInterviewJudge", () => {
  it("returns no notification but still provides a summary when there is no concrete signal", async () => {
    const judge = new MockInterviewJudge();

    const input: JudgeInput = {
      ...baseInput,
      transcript: [
        { speaker: "owner", message: "Hola, ¿cómo estás?" },
        { speaker: "visitor", message: "Todo bien, solo paseando por el parque." },
      ],
    };

    const decision = await judge.evaluate(input);

    expect(decision.should_notify).toBe(false);
    expect(typeof decision.summary_text).toBe("string");
    expect(decision.summary_text).toBeDefined();
    expect(decision.summary_text!.startsWith("Summary of agent interaction:")).toBe(true);
  });

  it("returns notification and a summary when there is a concrete meet signal", async () => {
    const judge = new MockInterviewJudge();

    const input: JudgeInput = {
      ...baseInput,
      transcript: [
        { speaker: "owner", message: "Deberíamos tomar un café para hablar de proyectos." },
        { speaker: "visitor", message: "Sí, feliz de reunirnos esta semana." },
      ],
    };

    const decision = await judge.evaluate(input);

    expect(decision.should_notify).toBe(true);
    expect(typeof decision.summary_text).toBe("string");
    expect(decision.summary_text).toBeDefined();
    expect(decision.summary_text!.startsWith("Summary of agent interaction:")).toBe(true);
  });
});


