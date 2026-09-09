from pipeline import pipeline
pipeline.run(open("examples/input.txt").read(),"examples/out")
print("Wrote examples/out/pipeline-output.json")
