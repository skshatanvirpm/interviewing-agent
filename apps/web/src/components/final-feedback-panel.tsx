"use client";

import type { CSSProperties } from "react";
import { BarChart3, ShieldAlert, TrendingUp } from "lucide-react";

import type { InterviewSession, PhaseEvaluation } from "@/lib/types";

type FinalFeedbackPanelProps = {
  session: InterviewSession;
};

const phaseOrder: PhaseEvaluation["phase"][] = [
  "phase_1_intro",
  "phase_2_deep_dive",
  "phase_3_breadth",
  "phase_4_factual",
  "phase_5_behavioral",
];

function formatDimensionLabel(value: string) {
  return value.replaceAll("_", " ");
}

function sortedEvaluations(session: InterviewSession) {
  return phaseOrder
    .map((phase) => session.phase_evaluations[phase])
    .filter((evaluation): evaluation is PhaseEvaluation => Boolean(evaluation));
}

export function FinalFeedbackPanel({ session }: FinalFeedbackPanelProps) {
  const evaluations = sortedEvaluations(session);
  const overallScore = session.final_feedback?.overall_score ?? session.scores.overall;
  const scoreDegrees = Math.max(0, Math.min(360, (overallScore ?? 0) * 36));
  const scoreStyle = {
    "--score-angle": `${scoreDegrees}deg`,
  } as CSSProperties;

  return (
    <section className="stack-lg">
      <section className="panel panel-glow review-hero">
        <div className="review-score-block" style={scoreStyle}>
          <div className="review-score-ring">
            <div className="review-score-core">
              <p className="summary-label">Overall</p>
              <p className="review-score-value">{overallScore ?? "-"}</p>
              <p className="review-score-denominator">/10</p>
            </div>
          </div>
        </div>

        <div className="stack-md review-summary">
          <div>
            <p className="eyebrow">Performance Review</p>
            <h1>Interview performance</h1>
          </div>
          <p className="supporting">
            {session.final_feedback?.overall_summary ??
              "There is not enough scored interview evidence yet to produce a complete review."}
          </p>

          <div className="review-pill-row">
            <div className="pill">
              <BarChart3 size={16} />
              {evaluations.length} scored phases
            </div>
            <div className="pill">
              <TrendingUp size={16} />
              {session.target_role}
            </div>
          </div>
        </div>
      </section>

      <section className="panel stack-md">
        <div>
          <p className="eyebrow">Phase Scores</p>
          <h2>Where you performed well and where to improve</h2>
        </div>
        <div className="stack-md">
          {evaluations.length ? (
            evaluations.map((evaluation) => {
              const phaseScore = evaluation.score ?? 0;
              return (
                <article className="phase-score-card" key={evaluation.phase}>
                  <div className="row row-between wrap gap-sm">
                    <div>
                      <p className="summary-label">{evaluation.label}</p>
                      <p className="summary-copy">{evaluation.suggestion}</p>
                    </div>
                    <p className="phase-score-number">{phaseScore}/10</p>
                  </div>
                  <div className="phase-bar-track">
                    <div
                      className="phase-bar-fill"
                      style={{ width: `${Math.max(8, phaseScore * 10)}%` }}
                    />
                  </div>
                  <div className="dimension-grid">
                    {Object.entries(evaluation.dimensions).map(([dimension, score]) => (
                      <div className="dimension-row" key={dimension}>
                        <span className="supporting">{formatDimensionLabel(dimension)}</span>
                        <span>{score}/10</span>
                      </div>
                    ))}
                  </div>
                </article>
              );
            })
          ) : (
            <article className="summary-card">
              <p className="summary-copy">
                Finish more of the interview to unlock phase-by-phase scoring.
              </p>
            </article>
          )}
        </div>
      </section>

      <div className="summary-grid review-lists">
        <article className="summary-card">
          <p className="summary-label">Strengths</p>
          <ul className="flat-list">
            {(session.final_feedback?.strengths.length
              ? session.final_feedback.strengths
              : ["No clear strengths detected yet."]
            ).map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </article>
        <article className="summary-card">
          <p className="summary-label">Weaknesses</p>
          <ul className="flat-list">
            {(session.final_feedback?.weaknesses.length
              ? session.final_feedback.weaknesses
              : ["No clear weaknesses detected yet."]
            ).map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </article>
        <article className="summary-card">
          <p className="summary-label">Suggestions</p>
          <ul className="flat-list">
            {(session.final_feedback?.suggestions.length
              ? session.final_feedback.suggestions
              : ["Complete more of the interview for concrete suggestions."]
            ).map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </article>
      </div>

      <div className="summary-grid review-lists">
        <article className="summary-card">
          <p className="summary-label">Role Alignment</p>
          <ul className="flat-list">
            {(session.final_feedback?.role_alignment.length
              ? session.final_feedback.role_alignment
              : ["Role-alignment notes will appear once the scored phases are complete."]
            ).map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </article>
        <article className="summary-card">
          <div className="row gap-sm">
            <ShieldAlert size={16} />
            <p className="summary-label">Interview Integrity</p>
          </div>
          <ul className="flat-list">
            {(
              session.final_feedback?.integrity_notes.length
                ? session.final_feedback.integrity_notes
                : ["No unusual integrity signals were detected."]
            ).map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </article>
      </div>
    </section>
  );
}
