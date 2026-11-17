import React from "react";
import {Composition} from "remotion";
import {PromoVideo, PromoProps} from "./PromoVideo";
import {VIDEO} from "./theme";

export const RemotionRoot: React.FC = () => (
  <>
    <Composition
      id="WisharoPromo"
      component={PromoVideo}
      durationInFrames={VIDEO.durationInFrames}
      fps={VIDEO.fps}
      width={VIDEO.width}
      height={VIDEO.height}
      defaultProps={{music: true} as PromoProps}
    />
    <Composition
      id="WisharoPromoNoMusic"
      component={PromoVideo}
      durationInFrames={VIDEO.durationInFrames}
      fps={VIDEO.fps}
      width={VIDEO.width}
      height={VIDEO.height}
      defaultProps={{music: false} as PromoProps}
    />
  </>
);
