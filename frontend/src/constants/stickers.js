import guineapigUrl from "../assets/images/guineapig.png";

export const stickerCategories = ["전체", "스티커", "프레임", "말풍선"];

export const decorations = [
  { id: "guineapig", icon: "guineapig", label: "기니피그", tone: "sticker-image guineapig-sticker", category: "스티커", imageSrc: guineapigUrl },
  { icon: "♡", tone: "pink", category: "스티커" },
  { icon: "★", tone: "purple", category: "스티커" },
  { icon: "✦", tone: "line", category: "스티커" },
  { icon: "♪", tone: "soft", category: "스티커" },
  { icon: "!", tone: "pink", category: "스티커" },
  { icon: "#", tone: "purple", category: "스티커" },
  { icon: "tape", tone: "masking-tape tape-lavender", category: "스티커" },
  { icon: "tape", tone: "masking-tape tape-rose", category: "스티커" },
  { icon: "tape", tone: "masking-tape tape-mint", category: "스티커" },
  { icon: "POLA", tone: "ink frame", category: "프레임" },
  { icon: "FILM", tone: "purple frame", category: "프레임" },
  { icon: "grid", tone: "soft bg", category: "프레임" },
  { icon: "dot", tone: "pink bg", category: "프레임" },
  { icon: "💬", label: "말풍선", tone: "bubble-normal", category: "말풍선", bubbleType: "normal" },
  { icon: "💭", label: "상상", tone: "bubble-thought", category: "말풍선", bubbleType: "thought" },
];
