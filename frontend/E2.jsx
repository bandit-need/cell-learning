import { useState, useEffect, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Timer from "@/components/game/Timer";
import DraggableCard from "@/components/game/DraggableCard";
import DropZone from "@/components/game/DropZone";
import ResultModal from "@/components/game/ResultModal";

const CELL_STAGES = [
  {
    id: "interphase",
    label: "Interphase",
    thaiLabel: "อินเตอร์เฟส",
    order: 1,
    color: "#6366f1",
    description: "เซลล์เตรียมพร้อม DNA ถูกจำลอง",
    image: "https://media.base44.com/images/public/69fcb7f2f2e1d9f3a57a7680/82fcfe895_generated_image.png",
  },
  {
    id: "prophase",
    label: "Prophase",
    thaiLabel: "โพรเฟส",
    order: 2,
    color: "#8b5cf6",
    description: "โครโมโซมหดตัวและมองเห็นได้",
    image: "https://media.base44.com/images/public/69fcb7f2f2e1d9f3a57a7680/1e5e42c29_generated_image.png",
  },
  {
    id: "metaphase",
    label: "Metaphase",
    thaiLabel: "เมทาเฟส",
    order: 3,
    color: "#ec4899",
    description: "โครโมโซมเรียงตรงกลางเซลล์",
    image: "https://media.base44.com/images/public/69fcb7f2f2e1d9f3a57a7680/c39da49e6_generated_image.png",
  },
  {
    id: "anaphase",
    label: "Anaphase",
    thaiLabel: "แอนาเฟส",
    order: 4,
    color: "#f59e0b",
    description: "โครโมโซมแยกไปแต่ละขั้ว",
    image: "https://media.base44.com/images/public/69fcb7f2f2e1d9f3a57a7680/1f9d4e398_generated_image.png",
  },
  {
    id: "telophase",
    label: "Telophase",
    thaiLabel: "เทโลเฟส",
    order: 5,
    color: "#10b981",
    description: "นิวเคลียสใหม่ 2 อันก่อตัว",
    image: "https://media.base44.com/images/public/69fcb7f2f2e1d9f3a57a7680/677098ac3_generated_image.png",
  },
  {
    id: "cytokinesis",
    label: "Cytokinesis",
    thaiLabel: "ไซโตไคนีซิส",
    order: 6,
    color: "#3b82f6",
    description: "ไซโทพลาสซึมแบ่ง เซลล์ลูก 2 เซลล์",
    image: "https://media.base44.com/images/public/69fcb7f2f2e1d9f3a57a7680/01dd5c005_generated_image.png",
  },
];

function shuffle(arr) {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

export default function CellGame() {
  const [cards, setCards] = useState(() => shuffle(CELL_STAGES));
  const [slots, setSlots] = useState(Array(CELL_STAGES.length).fill(null));
  const [dragging, setDragging] = useState(null); // { id, from: 'hand'|slotIndex }
  const [gameOver, setGameOver] = useState(false);
  const [score, setScore] = useState(null);
  const [time, setTime] = useState(0);
  const [running, setRunning] = useState(true);
  const timerRef = useRef(null);

  useEffect(() => {
    if (running && !gameOver) {
      timerRef.current = setInterval(() => setTime(t => t + 1), 1000);
    }
    return () => clearInterval(timerRef.current);
  }, [running, gameOver]);

  const handleDragStart = useCallback((id, from) => {
    setDragging({ id, from });
  }, []);

  const handleDropOnSlot = useCallback((slotIndex) => {
    if (!dragging) return;
    const { id, from } = dragging;
    const stage = CELL_STAGES.find(s => s.id === id);

    setSlots(prev => {
      const newSlots = [...prev];
      // If slot already has something, return it to hand
      if (newSlots[slotIndex] && newSlots[slotIndex].id !== id) {
        // occupied — swap or reject
        const displaced = newSlots[slotIndex];
        // put displaced back in hand
        setCards(c => {
          if (!c.find(x => x.id === displaced.id)) return [...c, displaced];
          return c;
        });
      }
      // Remove from old slot if came from slot
      if (typeof from === 'number') {
        newSlots[from] = null;
      }
      newSlots[slotIndex] = stage;
      return newSlots;
    });

    // Remove from hand if came from hand
    if (from === 'hand') {
      setCards(prev => prev.filter(c => c.id !== id));
    }

    setDragging(null);
  }, [dragging]);

  const handleDropOnHand = useCallback(() => {
    if (!dragging) return;
    const { id, from } = dragging;
    if (typeof from === 'number') {
      // return to hand
      setSlots(prev => {
        const newSlots = [...prev];
        newSlots[from] = null;
        return newSlots;
      });
      const stage = CELL_STAGES.find(s => s.id === id);
      setCards(prev => {
        if (!prev.find(c => c.id === id)) return [...prev, stage];
        return prev;
      });
    }
    setDragging(null);
  }, [dragging]);

  const handleSubmit = () => {
    const filled = slots.filter(Boolean).length;
    if (filled < CELL_STAGES.length) return;
    let correct = 0;
    slots.forEach((stage, i) => {
      if (stage && stage.order === i + 1) correct++;
    });
    setScore(correct);
    setGameOver(true);
    setRunning(false);
    clearInterval(timerRef.current);
  };

  const handleReset = () => {
    setCards(shuffle(CELL_STAGES));
    setSlots(Array(CELL_STAGES.length).fill(null));
    setDragging(null);
    setGameOver(false);
    setScore(null);
    setTime(0);
    setRunning(true);
  };

  const allFilled = slots.every(Boolean);

  return (
    <div className="min-h-screen bg-gradient-to-br from-violet-50 via-purple-50 to-blue-50 flex flex-col items-center py-6 px-4">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-2xl mb-6 flex items-center justify-between"
      >
        <div>
          <h1 className="text-2xl font-bold text-purple-800">🔬 เรียงขั้นตอนการแบ่งเซลล์</h1>
          <p className="text-sm text-purple-500 mt-0.5">ลากรูปมาวางในลำดับที่ถูกต้อง</p>
        </div>
        <Timer seconds={time} />
      </motion.div>

      {/* Drop zones */}
      <motion.div
        initial={{ opacity: 0, scale: 0.97 }}
        animate={{ opacity: 1, scale: 1 }}
        className="w-full max-w-2xl bg-white rounded-2xl shadow-lg border border-purple-100 p-4 mb-5"
      >
        <p className="text-xs font-semibold text-purple-400 uppercase tracking-wider mb-3">ลำดับขั้นตอน (1 → 6)</p>
        <div className="grid grid-cols-3 gap-3">
          {slots.map((stage, i) => (
            <DropZone
              key={i}
              index={i}
              stage={stage}
              onDrop={handleDropOnSlot}
              onDragStart={handleDragStart}
              isCorrect={gameOver && stage ? stage.order === i + 1 : null}
            />
          ))}
        </div>
      </motion.div>

      {/* Hand cards */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-2xl"
        onDragOver={e => e.preventDefault()}
        onDrop={handleDropOnHand}
      >
        <p className="text-xs font-semibold text-purple-400 uppercase tracking-wider mb-3">บัตรที่เหลือ</p>
        <div className="min-h-[120px] bg-white rounded-2xl border-2 border-dashed border-purple-200 p-3 flex flex-wrap gap-3 items-start">
          <AnimatePresence>
            {cards.map(stage => (
              <DraggableCard
                key={stage.id}
                stage={stage}
                onDragStart={handleDragStart}
                from="hand"
              />
            ))}
          </AnimatePresence>
          {cards.length === 0 && (
            <p className="text-purple-300 text-sm m-auto">วางบัตรทั้งหมดแล้ว ✓</p>
          )}
        </div>
      </motion.div>

      {/* Submit button */}
      <motion.button
        whileHover={{ scale: 1.03 }}
        whileTap={{ scale: 0.97 }}
        onClick={handleSubmit}
        disabled={!allFilled}
        className={`mt-6 px-8 py-3 rounded-2xl font-bold text-white text-lg shadow-lg transition-all
          ${allFilled
            ? "bg-gradient-to-r from-violet-600 to-purple-600 cursor-pointer hover:shadow-purple-300 hover:shadow-xl"
            : "bg-gray-300 cursor-not-allowed"
          }`}
      >
        ✅ ส่งคำตอบ
      </motion.button>

      <AnimatePresence>
        {gameOver && (
          <ResultModal
            score={score}
            total={CELL_STAGES.length}
            time={time}
            slots={slots}
            stages={CELL_STAGES}
            onReset={handleReset}
          />
        )}
      </AnimatePresence>
    </div>
  );
}