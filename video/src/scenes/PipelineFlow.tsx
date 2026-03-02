import { AbsoluteFill } from "remotion";
import { FlowNode } from "../components/FlowNode";
import { FlowArrow } from "../components/FlowArrow";
import { Caption } from "../components/Caption";
import { pipelineNodes } from "../data/mockData";

export const PipelineFlow: React.FC = () => {
  const framesPerNode = 16;

  return (
    <AbsoluteFill className="flex flex-col items-center justify-center bg-white">
      {/* Subtle grid pattern */}
      <div
        className="absolute inset-0 opacity-5"
        style={{
          backgroundImage:
            "linear-gradient(#e5e7eb 1px, transparent 1px), linear-gradient(90deg, #e5e7eb 1px, transparent 1px)",
          backgroundSize: "40px 40px",
        }}
      />

      <div className="relative z-10 flex items-center gap-0">
        {pipelineNodes.map((node, i) => (
          <div key={node.label} className="flex items-center">
            {i > 0 && (
              <FlowArrow
                delay={i * framesPerNode - 4}
                width={36}
              />
            )}
            <FlowNode
              label={node.label}
              color={node.color}
              delay={i * framesPerNode}
            />
          </div>
        ))}
      </div>

      <Caption text="Automated data pipeline" />
    </AbsoluteFill>
  );
};
