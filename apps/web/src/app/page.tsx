import { ResumeUploader } from "@/components/resume-uploader";

export default function HomePage() {
  return (
    <main className="page-shell">
      <section className="hero hero-simple" id="bootstrap">
        <div className="hero-copy">
          <p className="eyebrow">Machine Learning Interview Agent</p>
          <h1>Parse your resume. Start the interview. Review your performance.</h1>
          <p className="supporting hero-supporting">
            Keep the experience focused: one clear start action, one clear end action, and a
            dedicated review page after the interview.
          </p>
        </div>
      </section>

      <div className="stack-lg">
        <ResumeUploader />
      </div>
    </main>
  );
}
