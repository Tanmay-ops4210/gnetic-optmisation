import PageHeader from '../components/PageHeader'

export default function DocsPage() {
  return (
    <div className="p-4 md:p-6 max-w-4xl mx-auto space-y-8">
      <PageHeader title="Documentation" subtitle="How to use AutoML Genetic Optimizer" />

      <div className="prose prose-invert max-w-none prose-slate">
        <div className="card space-y-4">
          <h2 className="text-xl font-bold text-white mb-2">1. Introduction</h2>
          <p className="text-slate-300 text-sm leading-relaxed">
            AutoML Genetic Optimizer automates the process of finding the best machine learning model and hyperparameters for your dataset. It utilizes evolutionary algorithms (Genetic Algorithm) combined with random search to efficiently explore the hyperparameter space.
          </p>
        </div>

        <div className="card space-y-4">
          <h2 className="text-xl font-bold text-white mb-2">2. Uploading Data</h2>
          <p className="text-slate-300 text-sm leading-relaxed">
            Navigate to the <strong>Dataset</strong> page and upload any standard CSV file. The system will automatically detect the columns, their data types, and any missing values. You can then select your target variable and the features you want to use for training.
          </p>
        </div>

        <div className="card space-y-4">
          <h2 className="text-xl font-bold text-white mb-2">3. Configuring the Optimizer</h2>
          <p className="text-slate-300 text-sm leading-relaxed">
            On the <strong>Optimization</strong> page, you can customize the evolutionary process:
          </p>
          <ul className="list-disc pl-5 text-slate-300 text-sm space-y-2">
            <li><strong>Population Size:</strong> Number of candidate models evaluated per generation.</li>
            <li><strong>Generations:</strong> How many times the population is evolved.</li>
            <li><strong>Mutation & Crossover:</strong> Rates controlling the randomness and genetic mixing of hyperparameters.</li>
            <li><strong>Selection Method:</strong> How the best models are selected for the next generation (Tournament vs Roulette).</li>
          </ul>
        </div>

        <div className="card space-y-4">
          <h2 className="text-xl font-bold text-white mb-2">4. Results & Predictions</h2>
          <p className="text-slate-300 text-sm leading-relaxed">
            After the genetic algorithm completes, you will see the <strong>Results</strong> page showing the best model, its hyperparameters, and the overall improvement over a baseline model. You can seamlessly switch to the <strong>Prediction</strong> tab to use the newly discovered model on fresh inputs.
          </p>
        </div>
      </div>
    </div>
  )
}
