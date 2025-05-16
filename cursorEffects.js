export function characterCursor(options) {
    let hasWrapperEl = options && options.element;
    let element = hasWrapperEl || document.body;
    let possibleCharacters = options?.characters || ["h", "e", "l", "l", "o"];
    const colors = options?.colors || ["#6622CC", "#A755C2", "#B07C9E", "#B59194", "#D2A1B8"];
    let cursorOffset = options?.cursorOffset || { x: 0, y: 0 };
    let width = window.innerWidth;
    let height = window.innerHeight;
    let cursor = { x: width / 2, y: width / 2 };
    let particles = [];
    let canvas, context, animationFrame;
    let font = options?.font || "15px serif";
    let canvImages = [];
  
    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
    prefersReducedMotion.onchange = () => {
      if (prefersReducedMotion.matches) destroy();
      else init();
    };
  
    function randomSign() {
      return Math.random() < 0.5 ? -1 : 1;
    }
  
    function characterLifeSpan() {
      return Math.floor(Math.random() * 60 + 80);
    }
  
    function initialVelocity() {
      return { x: randomSign() * Math.random() * 5, y: randomSign() * Math.random() * 5 };
    }
  
    function velocityChange(age, lifeSpan) {
      return randomSign() / 30;
    }
  
    function scaling(age, lifeSpan) {
      let lifeLeft = lifeSpan - age;
      return Math.max((lifeLeft / lifeSpan) * 2, 0);
    }
  
    function rotationDegrees(age, lifeSpan) {
      let lifeLeft = lifeSpan - age;
      return lifeLeft / 5;
    }
  
    function init() {
      if (prefersReducedMotion.matches) return false;
  
      canvas = document.createElement("canvas");
      context = canvas.getContext("2d");
      canvas.style.position = hasWrapperEl ? "absolute" : "fixed";
      canvas.style.top = "0px";
      canvas.style.left = "0px";
      canvas.style.pointerEvents = "none";
      (hasWrapperEl ? element : document.body).appendChild(canvas);
      canvas.width = hasWrapperEl ? element.clientWidth : width;
      canvas.height = hasWrapperEl ? element.clientHeight : height;
      context.font = font;
      context.textBaseline = "middle";
      context.textAlign = "center";
  
      possibleCharacters.forEach((char) => {
        let m = context.measureText(char);
        let c = document.createElement("canvas");
        let ctx = c.getContext("2d");
        c.width = m.width;
        c.height = m.actualBoundingBoxAscent * 2.5;
        ctx.textAlign = "center";
        ctx.font = font;
        ctx.textBaseline = "middle";
        ctx.fillStyle = colors[Math.floor(Math.random() * colors.length)];
        ctx.fillText(char, c.width / 2, m.actualBoundingBoxAscent);
        canvImages.push(c);
      });
  
      bindEvents();
      loop();
    }
  
    function bindEvents() {
      element.addEventListener("mousemove", onMouseMove);
      element.addEventListener("touchmove", onTouchMove, { passive: true });
      element.addEventListener("touchstart", onTouchMove, { passive: true });
      window.addEventListener("resize", onResize);
    }
  
    function onResize() {
      width = window.innerWidth;
      height = window.innerHeight;
      canvas.width = hasWrapperEl ? element.clientWidth : width;
      canvas.height = hasWrapperEl ? element.clientHeight : height;
    }
  
    function onTouchMove(e) {
      if (e.touches.length > 0) {
        for (let i = 0; i < e.touches.length; i++) {
          addParticle(e.touches[i].clientX, e.touches[i].clientY);
        }
      }
    }
  
    function onMouseMove(e) {
      const rect = hasWrapperEl ? element.getBoundingClientRect() : { left: 0, top: 0 };
      cursor.x = e.clientX - rect.left;
      cursor.y = e.clientY - rect.top;
      addParticle(cursor.x, cursor.y);
    }
  
    function addParticle(x, y) {
      particles.push(new Particle(x, y, canvImages[Math.floor(Math.random() * canvImages.length)]));
    }
  
    function updateParticles() {
      if (particles.length === 0) return;
      context.clearRect(0, 0, width, height);
      for (let p of particles) p.update(context);
      particles = particles.filter(p => p.lifeSpan > 0);
    }
  
    function loop() {
      updateParticles();
      animationFrame = requestAnimationFrame(loop);
    }
  
    function destroy() {
      if (canvas && canvas.parentNode) canvas.remove();
      cancelAnimationFrame(animationFrame);
      element.removeEventListener("mousemove", onMouseMove);
      element.removeEventListener("touchmove", onTouchMove);
      element.removeEventListener("touchstart", onTouchMove);
      window.removeEventListener("resize", onResize);
    }
  
    function Particle(x, y, img) {
      this.rotationSign = randomSign();
      this.age = 0;
      this.lifeSpan = characterLifeSpan();
      this.velocity = initialVelocity();
      this.position = { x: x + cursorOffset.x, y: y + cursorOffset.y };
      this.canv = img;
  
      this.update = function (ctx) {
        this.position.x += this.velocity.x;
        this.position.y += this.velocity.y;
        this.velocity.x += velocityChange(this.age, this.lifeSpan);
        this.velocity.y += velocityChange(this.age, this.lifeSpan);
        this.age++;
        this.lifeSpan--;
  
        const scale = scaling(this.age, this.lifeSpan + this.age);
        const deg = this.rotationSign * rotationDegrees(this.age, this.lifeSpan + this.age);
        const rad = deg * (Math.PI / 180);
  
        ctx.translate(this.position.x, this.position.y);
        ctx.rotate(rad);
        ctx.drawImage(this.canv, (-this.canv.width / 2) * scale, -this.canv.height / 2, this.canv.width * scale, this.canv.height * scale);
        ctx.rotate(-rad);
        ctx.translate(-this.position.x, -this.position.y);
      };
    }
  
    init();
    return { destroy };
  }













  export function bubbleCursor(options) {
    let hasWrapperEl = options && options.element;
    let element = hasWrapperEl || document.body;
  
    let width = window.innerWidth;
    let height = window.innerHeight;
    let cursor = { x: width / 2, y: width / 2 };
    let particles = [];
    let canvas, context, animationFrame;
  
    let canvImages = [];
  
    const prefersReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)"
    );
  
    // Re-initialise or destroy the cursor when the prefers-reduced-motion setting changes
    prefersReducedMotion.onchange = () => {
      if (prefersReducedMotion.matches) {
        destroy();
      } else {
        init();
      }
    };
  
    function init() {
      // Don't show the cursor trail if the user has prefers-reduced-motion enabled
      if (prefersReducedMotion.matches) {
        console.log(
          "This browser has prefers reduced motion turned on, so the cursor did not init"
        );
        return false;
      }
  
      canvas = document.createElement("canvas");
      context = canvas.getContext("2d");
  
      canvas.style.top = "0px";
      canvas.style.left = "0px";
      canvas.style.pointerEvents = "none";
  
      if (hasWrapperEl) {
        canvas.style.position = "absolute";
        element.appendChild(canvas);
        canvas.width = element.clientWidth;
        canvas.height = element.clientHeight;
      } else {
        canvas.style.position = "fixed";
        document.body.appendChild(canvas);
        canvas.width = width;
        canvas.height = height;
      }
  
      bindEvents();
      loop();
    }
  
    // Bind events that are needed
    function bindEvents() {
      element.addEventListener("mousemove", onMouseMove);
      element.addEventListener("touchmove", onTouchMove, { passive: true });
      element.addEventListener("touchstart", onTouchMove, { passive: true });
      window.addEventListener("resize", onWindowResize);
    }
  
    function onWindowResize(e) {
      width = window.innerWidth;
      height = window.innerHeight;
  
      if (hasWrapperEl) {
        canvas.width = element.clientWidth;
        canvas.height = element.clientHeight;
      } else {
        canvas.width = width;
        canvas.height = height;
      }
    }
  
    function onTouchMove(e) {
      if (e.touches.length > 0) {
        for (let i = 0; i < e.touches.length; i++) {
          addParticle(
            e.touches[i].clientX,
            e.touches[i].clientY,
            canvImages[Math.floor(Math.random() * canvImages.length)]
          );
        }
      }
    }
  
    function onMouseMove(e) {
      if (hasWrapperEl) {
        const boundingRect = element.getBoundingClientRect();
        cursor.x = e.clientX - boundingRect.left;
        cursor.y = e.clientY - boundingRect.top;
      } else {
        cursor.x = e.clientX;
        cursor.y = e.clientY;
      }
  
      addParticle(cursor.x, cursor.y);
    }
  
    function addParticle(x, y, img) {
      particles.push(new Particle(x, y, img));
    }
  
    function updateParticles() {
      if (particles.length == 0) {
        return;
      }
  
      context.clearRect(0, 0, width, height);
  
      // Update
      for (let i = 0; i < particles.length; i++) {
        particles[i].update(context);
      }
  
      // Remove dead particles
      for (let i = particles.length - 1; i >= 0; i--) {
        if (particles[i].lifeSpan < 0) {
          particles.splice(i, 1);
        }
      }
  
      if (particles.length == 0) {
        context.clearRect(0, 0, width, height);
      }
    }
  
    function loop() {
      updateParticles();
      animationFrame = requestAnimationFrame(loop);
    }
  
    function destroy() {
      canvas.remove();
      cancelAnimationFrame(animationFrame);
      element.removeEventListener("mousemove", onMouseMove);
      element.removeEventListener("touchmove", onTouchMove);
      element.removeEventListener("touchstart", onTouchMove);
      window.addEventListener("resize", onWindowResize);
    };
  
    function Particle(x, y, canvasItem) {
      const lifeSpan = Math.floor(Math.random() * 60 + 60);
      this.initialLifeSpan = lifeSpan; //
      this.lifeSpan = lifeSpan; //ms
      this.velocity = {
        x: (Math.random() < 0.5 ? -1 : 1) * (Math.random() / 10),
        y: -0.4 + Math.random() * -1,
      };
      this.position = { x: x, y: y };
      this.canv = canvasItem;
  
      this.baseDimension = 4;
  
      this.update = function (context) {
        this.position.x += this.velocity.x;
        this.position.y += this.velocity.y;
        this.velocity.x += ((Math.random() < 0.5 ? -1 : 1) * 2) / 75;
        this.velocity.y -= Math.random() / 600;
        this.lifeSpan--;
  
        const scale =
          0.2 + (this.initialLifeSpan - this.lifeSpan) / this.initialLifeSpan;
  
        context.fillStyle = "#e6f1f7";
        context.strokeStyle = "#3a92c5";
        context.beginPath();
        context.arc(
          this.position.x - (this.baseDimension / 2) * scale,
          this.position.y - this.baseDimension / 2,
          this.baseDimension * scale,
          0,
          2 * Math.PI
        );
  
        context.stroke();
        context.fill();
  
        context.closePath();
      };
    }
  
    init();
  
  
    return {
      destroy: destroy
    }
  }
  








// The clock effect has been translated over from this old
// code, to modern js & canvas
// - https://web.archive.org/web/20041026003308/http://rainbow.arch.scriptmania.com/scripts/mouse_clock.html

export function clockCursor(options) {
    let hasWrapperEl = options && options.element;
    let element = hasWrapperEl || document.body;
  
    let width = window.innerWidth;
    let height = window.innerHeight;
    let cursor = { x: width / 2, y: width / 2 };
    let canvas, context, animationFrame;
  
    const dateColor = (options && options.dateColor) || "blue";
    const faceColor = (options && options.faceColor) || "black";
    const secondsColor = (options && options.secondsColor) || "red";
    const minutesColor = (options && options.minutesColor) || "black";
    const hoursColor = (options && options.hoursColor) || "black";
  
    const del = 0.4;
  
    const theDays = (options && options.theDays) || [
      "SUNDAY",
      "MONDAY",
      "TUESDAY",
      "WEDNESDAY",
      "THURSDAY",
      "FRIDAY",
      "SATURDAY",
    ];
  
    const theMonths = (options && options.theMonths) || [
      "JANUARY",
      "FEBRUARY",
      "MARCH",
      "APRIL",
      "MAY",
      "JUNE",
      "JULY",
      "AUGUST",
      "SEPTEMBER",
      "OCTOBER",
      "NOVEMBER",
      "DECEMBER",
    ];
  
    let date = new Date();
    let day = date.getDate();
    let year = date.getYear() + 1900; // Year
  
    // Prepare particle arrays
    const dateInWords = (
      " " +
      theDays[date.getDay()] +
      " " +
      day +
      " " +
      theMonths[date.getMonth()] +
      " " +
      year
    ).split("");
  
    const clockNumbers = [
      "3",
      "4",
      "5",
      "6",
      "7",
      "8",
      "9",
      "10",
      "11",
      "12",
      "1",
      "2",
    ];
  
    const F = clockNumbers.length; // todo: why
  
    const hourHand = ["•", "•", "•"];
    const minuteHand = ["•", "•", "•", "•"];
    const secondHand = ["•", "•", "•", "•", "•"];
  
    const siz = 45;
    const eqf = 360 / F;
    const eqd = 360 / dateInWords.length;
    const han = siz / 6.5;
    const ofy = 0;
    const ofx = 0;
    const ofst = 0;
  
    const dy = [];
    const dx = [];
    const zy = [];
    const zx = [];
  
    const tmps = [];
    const tmpm = [];
    const tmph = [];
    const tmpf = [];
    const tmpd = [];
  
    var sum =
      parseInt(
        dateInWords.length +
          F +
          hourHand.length +
          minuteHand.length +
          secondHand.length
      ) + 1;
  
    const prefersReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)"
    );
  
    // Re-initialise or destroy the cursor when the prefers-reduced-motion setting changes
    prefersReducedMotion.onchange = () => {
      if (prefersReducedMotion.matches) {
        destroy();
      } else {
        init();
      }
    };
  
    function init() {
      // Don't show the cursor trail if the user has prefers-reduced-motion enabled
      if (prefersReducedMotion.matches) {
        console.log(
          "This browser has prefers reduced motion turned on, so the cursor did not init"
        );
        return false;
      }
  
      canvas = document.createElement("canvas");
      context = canvas.getContext("2d");
  
      canvas.style.top = "0px";
      canvas.style.left = "0px";
      canvas.style.pointerEvents = "none";
  
      if (hasWrapperEl) {
        canvas.style.position = "absolute";
        element.appendChild(canvas);
        canvas.width = element.clientWidth;
        canvas.height = element.clientHeight;
      } else {
        canvas.style.position = "fixed";
        document.body.appendChild(canvas);
        canvas.width = width;
        canvas.height = height;
      }
  
      context.font = "10px sans-serif";
      context.textAlign = "center";
      context.textBaseline = "middle";
  
      // indivdual positions of the movement and movement deltas
      for (let i = 0; i < sum; i++) {
        dy[i] = 0;
        dx[i] = 0;
        zy[i] = 0;
        zx[i] = 0;
      }
  
      // Date in Words
      for (let i = 0; i < dateInWords.length; i++) {
        tmpd[i] = {
          color: dateColor,
          value: dateInWords[i],
        };
      }
  
      // Face!
      for (let i = 0; i < clockNumbers.length; i++) {
        tmpf[i] = {
          color: faceColor,
          value: clockNumbers[i],
        };
      }
  
      // Hour
      for (let i = 0; i < hourHand.length; i++) {
        tmph[i] = {
          color: hoursColor,
          value: hourHand[i],
        };
      }
  
      // Minutes
      for (let i = 0; i < minuteHand.length; i++) {
        tmpm[i] = {
          color: minutesColor,
          value: minuteHand[i],
        };
      }
  
      // Seconds
      for (let i = 0; i < secondHand.length; i++) {
        tmps[i] = {
          color: secondsColor,
          value: secondHand[i],
        };
      }
  
      bindEvents();
      loop();
    }
  
    // Bind events that are needed
    function bindEvents() {
      element.addEventListener("mousemove", onMouseMove);
      element.addEventListener("touchmove", onTouchMove, { passive: true });
      element.addEventListener("touchstart", onTouchMove, { passive: true });
      window.addEventListener("resize", onWindowResize);
    }
  
    function onWindowResize(e) {
      width = window.innerWidth;
      height = window.innerHeight;
  
      if (hasWrapperEl) {
        canvas.width = element.clientWidth;
        canvas.height = element.clientHeight;
      } else {
        canvas.width = width;
        canvas.height = height;
      }
    }
  
    function onTouchMove(e) {
      if (e.touches.length > 0) {
        if (hasWrapperEl) {
          const boundingRect = element.getBoundingClientRect();
          cursor.x = e.touches[0].clientX - boundingRect.left;
          cursor.y = e.touches[0].clientY - boundingRect.top;
        } else {
          cursor.x = e.touches[0].clientX;
          cursor.y = e.touches[0].clientY;
        }
      }
    }
  
    function onMouseMove(e) {
      if (hasWrapperEl) {
        const boundingRect = element.getBoundingClientRect();
        cursor.x = e.clientX - boundingRect.left;
        cursor.y = e.clientY - boundingRect.top;
      } else {
        cursor.x = e.clientX;
        cursor.y = e.clientY;
      }
    }
  
    function updatePositions() {
      let widthBuffer = 80;
  
      zy[0] = Math.round((dy[0] += (cursor.y - dy[0]) * del));
      zx[0] = Math.round((dx[0] += (cursor.x - dx[0]) * del));
      for (let i = 1; i < sum; i++) {
        zy[i] = Math.round((dy[i] += (zy[i - 1] - dy[i]) * del));
        zx[i] = Math.round((dx[i] += (zx[i - 1] - dx[i]) * del));
        if (dy[i - 1] >= height - 80) dy[i - 1] = height - 80;
        if (dx[i - 1] >= width - widthBuffer) dx[i - 1] = width - widthBuffer;
      }
    }
  
    function updateParticles() {
      context.clearRect(0, 0, width, height);
  
      const time = new Date();
      const secs = time.getSeconds();
      const sec = (Math.PI * (secs - 15)) / 30;
      const mins = time.getMinutes();
      const min = (Math.PI * (mins - 15)) / 30;
      const hrs = time.getHours();
      const hr =
        (Math.PI * (hrs - 3)) / 6 + (Math.PI * parseInt(time.getMinutes())) / 360;
  
      // Date
      for (let i = 0; i < tmpd.length; i++) {
        tmpd[i].y =
          dy[i] + siz * 1.5 * Math.sin(-sec + (i * eqd * Math.PI) / 180);
        tmpd[i].x =
          dx[i] + siz * 1.5 * Math.cos(-sec + (i * eqd * Math.PI) / 180);
  
        context.fillStyle = tmpd[i].color;
        context.fillText(tmpd[i].value, tmpd[i].x, tmpd[i].y);
      }
  
      // Face
      for (let i = 0; i < tmpf.length; i++) {
        tmpf[i].y =
          dy[tmpd.length + i] + siz * Math.sin((i * eqf * Math.PI) / 180);
        tmpf[i].x =
          dx[tmpd.length + i] + siz * Math.cos((i * eqf * Math.PI) / 180);
  
        context.fillStyle = tmpf[i].color;
        context.fillText(tmpf[i].value, tmpf[i].x, tmpf[i].y);
      }
  
      // Hours
      for (let i = 0; i < tmph.length; i++) {
        tmph[i].y = dy[tmpd.length + F + i] + ofy + i * han * Math.sin(hr);
        tmph[i].x = dx[tmpd.length + F + i] + ofx + i * han * Math.cos(hr);
  
        context.fillStyle = tmph[i].color;
        context.fillText(tmph[i].value, tmph[i].x, tmph[i].y);
      }
  
      // Minutes
      for (let i = 0; i < tmpm.length; i++) {
        tmpm[i].y =
          dy[tmpd.length + F + tmph.length + i] + ofy + i * han * Math.sin(min);
  
        tmpm[i].x =
          dx[tmpd.length + F + tmph.length + i] + ofx + i * han * Math.cos(min);
  
        context.fillStyle = tmpm[i].color;
        context.fillText(tmpm[i].value, tmpm[i].x, tmpm[i].y);
      }
  
      // Seconds
      for (let i = 0; i < tmps.length; i++) {
        tmps[i].y =
          dy[tmpd.length + F + tmph.length + tmpm.length + i] +
          ofy +
          i * han * Math.sin(sec);
  
        tmps[i].x =
          dx[tmpd.length + F + tmph.length + tmpm.length + i] +
          ofx +
          i * han * Math.cos(sec);
  
        context.fillStyle = tmps[i].color;
        context.fillText(tmps[i].value, tmps[i].x, tmps[i].y);
      }
    }
  
    function loop() {
      updatePositions();
      updateParticles();
  
      animationFrame = requestAnimationFrame(loop);
    }
  
    function destroy() {
      canvas.remove();
      cancelAnimationFrame(animationFrame);
      element.removeEventListener("mousemove", onMouseMove);
      element.removeEventListener("touchmove", onTouchMove);
      element.removeEventListener("touchstart", onTouchMove);
      window.addEventListener("resize", onWindowResize);
    }
  
    init();
  
    return {
      destroy: destroy,
    };
  }











  export function emojiCursor(options) {
    const possibleEmoji = (options && options.emoji) || ["😀", "😂", "😆", "😊"];
    const delay = (options && options.delay) || 16;
    let hasWrapperEl = options && options.element;
    let element = hasWrapperEl || document.body;
  
    let width = window.innerWidth;
    let height = window.innerHeight;
    const cursor = { x: width / 2, y: width / 2 };
    const lastPos = { x: width / 2, y: width / 2 };
    let lastTimestamp = 0;
    const particles = [];
    const canvImages = [];
    let canvas, context, animationFrame;
  
    const prefersReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)"
    );
  
    // Re-initialise or destroy the cursor when the prefers-reduced-motion setting changes
    prefersReducedMotion.onchange = () => {
      if (prefersReducedMotion.matches) {
        destroy();
      } else {
        init();
      }
    };
  
    function init() {
      // Don't show the cursor trail if the user has prefers-reduced-motion enabled
      if (prefersReducedMotion.matches) {
        console.log(
          "This browser has prefers reduced motion turned on, so the cursor did not init"
        );
        return false;
      }
  
      canvas = document.createElement("canvas");
      context = canvas.getContext("2d");
  
      canvas.style.top = "0px";
      canvas.style.left = "0px";
      canvas.style.pointerEvents = "none";
  
      if (hasWrapperEl) {
        canvas.style.position = "absolute";
        element.appendChild(canvas);
        canvas.width = element.clientWidth;
        canvas.height = element.clientHeight;
      } else {
        canvas.style.position = "fixed";
        document.body.appendChild(canvas);
        canvas.width = width;
        canvas.height = height;
      }
  
      context.font = "21px serif";
      context.textBaseline = "middle";
      context.textAlign = "center";
  
      possibleEmoji.forEach((emoji) => {
        let measurements = context.measureText(emoji);
        let bgCanvas = document.createElement("canvas");
        let bgContext = bgCanvas.getContext("2d");
  
        bgCanvas.width = measurements.width;
        bgCanvas.height = measurements.actualBoundingBoxAscent * 2;
  
        bgContext.textAlign = "center";
        bgContext.font = "21px serif";
        bgContext.textBaseline = "middle";
        bgContext.fillText(
          emoji,
          bgCanvas.width / 2,
          measurements.actualBoundingBoxAscent
        );
  
        canvImages.push(bgCanvas);
      });
  
      bindEvents();
      loop();
    }
  
    // Bind events that are needed
    function bindEvents() {
      element.addEventListener("mousemove", onMouseMove, { passive: true });
      element.addEventListener("touchmove", onTouchMove, { passive: true });
      element.addEventListener("touchstart", onTouchMove, { passive: true });
      window.addEventListener("resize", onWindowResize);
    }
  
    function onWindowResize(e) {
      width = window.innerWidth;
      height = window.innerHeight;
  
      if (hasWrapperEl) {
        canvas.width = element.clientWidth;
        canvas.height = element.clientHeight;
      } else {
        canvas.width = width;
        canvas.height = height;
      }
    }
  
    function onTouchMove(e) {
      if (e.touches.length > 0) {
        for (let i = 0; i < e.touches.length; i++) {
          addParticle(
            e.touches[i].clientX,
            e.touches[i].clientY,
            canvImages[Math.floor(Math.random() * canvImages.length)]
          );
        }
      }
    }
  
    function onMouseMove(e) {
      // Dont run too fast
      if (e.timeStamp - lastTimestamp < delay) {
        return;
      }
  
      window.requestAnimationFrame(() => {
        if (hasWrapperEl) {
          const boundingRect = element.getBoundingClientRect();
          cursor.x = e.clientX - boundingRect.left;
          cursor.y = e.clientY - boundingRect.top;
        } else {
          cursor.x = e.clientX;
          cursor.y = e.clientY;
        }
  
        const distBetweenPoints = Math.hypot(
          cursor.x - lastPos.x,
          cursor.y - lastPos.y
        );
  
        if (distBetweenPoints > 1) {
          addParticle(
            cursor.x,
            cursor.y,
            canvImages[Math.floor(Math.random() * possibleEmoji.length)]
          );
  
          lastPos.x = cursor.x;
          lastPos.y = cursor.y;
          lastTimestamp = e.timeStamp;
        }
      });
    }
  
    function addParticle(x, y, img) {
      particles.push(new Particle(x, y, img));
    }
  
    function updateParticles() {
      if (particles.length == 0) {
        return;
      }
  
      context.clearRect(0, 0, width, height);
  
      // Update
      for (let i = 0; i < particles.length; i++) {
        particles[i].update(context);
      }
  
      // Remove dead particles
      for (let i = particles.length - 1; i >= 0; i--) {
        if (particles[i].lifeSpan < 0) {
          particles.splice(i, 1);
        }
      }
  
      if (particles.length == 0) {
        context.clearRect(0, 0, width, height);
      }
    }
  
    function loop() {
      updateParticles();
      animationFrame = requestAnimationFrame(loop);
    }
  
    function destroy() {
      canvas.remove();
      cancelAnimationFrame(animationFrame);
      element.removeEventListener("mousemove", onMouseMove);
      element.removeEventListener("touchmove", onTouchMove);
      element.removeEventListener("touchstart", onTouchMove);
      window.addEventListener("resize", onWindowResize);
    }
  
    /**
     * Particles
     */
  
    function Particle(x, y, canvasItem) {
      const lifeSpan = Math.floor(Math.random() * 60 + 80);
      this.initialLifeSpan = lifeSpan; //
      this.lifeSpan = lifeSpan; //ms
      this.velocity = {
        x: (Math.random() < 0.5 ? -1 : 1) * (Math.random() / 2),
        y: Math.random() * 0.4 + 0.8,
      };
      this.position = { x: x, y: y };
      this.canv = canvasItem;
  
      this.update = function (context) {
        this.position.x += this.velocity.x;
        this.position.y += this.velocity.y;
        this.lifeSpan--;
  
        this.velocity.y += 0.05;
  
        const scale = Math.max(this.lifeSpan / this.initialLifeSpan, 0);
  
        context.drawImage(
          this.canv,
          this.position.x - (this.canv.width / 2) * scale,
          this.position.y - this.canv.height / 2,
          this.canv.width * scale,
          this.canv.height * scale
        );
      };
    }
  
    init();
  
    return {
      destroy: destroy,
    };
  }






  export function fairyDustCursor(options) {
    let possibleColors = (options && options.colors) || [
      "#D61C59",
      "#E7D84B",
      "#1B8798",
    ];
    let hasWrapperEl = options && options.element;
    let element = hasWrapperEl || document.body;
  
    let width = window.innerWidth;
    let height = window.innerHeight;
    const cursor = { x: width / 2, y: width / 2 };
    const lastPos = { x: width / 2, y: width / 2 };
    const particles = [];
    const canvImages = [];
    let canvas, context, animationFrame;
  
    const char = "*";
  
    const prefersReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)"
    );
  
    // Re-initialise or destroy the cursor when the prefers-reduced-motion setting changes
    prefersReducedMotion.onchange = () => {
      if (prefersReducedMotion.matches) {
        destroy();
      } else {
        init();
      }
    };
  
    function init() {
      // Don't show the cursor trail if the user has prefers-reduced-motion enabled
      if (prefersReducedMotion.matches) {
        console.log(
          "This browser has prefers reduced motion turned on, so the cursor did not init"
        );
        return false;
      }
  
      canvas = document.createElement("canvas");
      context = canvas.getContext("2d");
      canvas.style.top = "0px";
      canvas.style.left = "0px";
      canvas.style.pointerEvents = "none";
  
      if (hasWrapperEl) {
        canvas.style.position = "absolute";
        element.appendChild(canvas);
        canvas.width = element.clientWidth;
        canvas.height = element.clientHeight;
      } else {
        canvas.style.position = "fixed";
        element.appendChild(canvas);
        canvas.width = width;
        canvas.height = height;
      }
  
      context.font = "21px serif";
      context.textBaseline = "middle";
      context.textAlign = "center";
  
      possibleColors.forEach((color) => {
        let measurements = context.measureText(char);
        let bgCanvas = document.createElement("canvas");
        let bgContext = bgCanvas.getContext("2d");
  
        bgCanvas.width = measurements.width;
        bgCanvas.height =
          measurements.actualBoundingBoxAscent +
          measurements.actualBoundingBoxDescent;
  
        bgContext.fillStyle = color;
        bgContext.textAlign = "center";
        bgContext.font = "21px serif";
        bgContext.textBaseline = "middle";
        bgContext.fillText(
          char,
          bgCanvas.width / 2,
          measurements.actualBoundingBoxAscent
        );
  
        canvImages.push(bgCanvas);
      });
  
      bindEvents();
      loop();
    }
  
    // Bind events that are needed
    function bindEvents() {
      element.addEventListener("mousemove", onMouseMove);
      element.addEventListener("touchmove", onTouchMove, { passive: true });
      element.addEventListener("touchstart", onTouchMove, { passive: true });
      window.addEventListener("resize", onWindowResize);
    }
  
    function onWindowResize(e) {
      width = window.innerWidth;
      height = window.innerHeight;
  
      if (hasWrapperEl) {
        canvas.width = element.clientWidth;
        canvas.height = element.clientHeight;
      } else {
        canvas.width = width;
        canvas.height = height;
      }
    }
  
    function onTouchMove(e) {
      if (e.touches.length > 0) {
        for (let i = 0; i < e.touches.length; i++) {
          addParticle(
            e.touches[i].clientX,
            e.touches[i].clientY,
            canvImages[Math.floor(Math.random() * canvImages.length)]
          );
        }
      }
    }
  
    function onMouseMove(e) {
      window.requestAnimationFrame(() => {
        if (hasWrapperEl) {
          const boundingRect = element.getBoundingClientRect();
          cursor.x = e.clientX - boundingRect.left;
          cursor.y = e.clientY - boundingRect.top;
        } else {
          cursor.x = e.clientX;
          cursor.y = e.clientY;
        }
  
        const distBetweenPoints = Math.hypot(
          cursor.x - lastPos.x,
          cursor.y - lastPos.y
        );
  
        if (distBetweenPoints > 1.5) {
          addParticle(
            cursor.x,
            cursor.y,
            canvImages[Math.floor(Math.random() * possibleColors.length)]
          );
  
          lastPos.x = cursor.x;
          lastPos.y = cursor.y;
        }
      });
    }
  
    function addParticle(x, y, color) {
      particles.push(new Particle(x, y, color));
    }
  
    function updateParticles() {
      if (particles.length == 0) {
        return;
      }
  
      context.clearRect(0, 0, width, height);
  
      // Update
      for (let i = 0; i < particles.length; i++) {
        particles[i].update(context);
      }
  
      // Remove dead particles
      for (let i = particles.length - 1; i >= 0; i--) {
        if (particles[i].lifeSpan < 0) {
          particles.splice(i, 1);
        }
      }
  
      if (particles.length == 0) {
        context.clearRect(0, 0, width, height);
      }
    }
  
    function loop() {
      updateParticles();
      animationFrame = requestAnimationFrame(loop);
    }
  
    function destroy() {
      canvas.remove();
      cancelAnimationFrame(animationFrame);
      element.removeEventListener("mousemove", onMouseMove);
      element.removeEventListener("touchmove", onTouchMove);
      element.removeEventListener("touchstart", onTouchMove);
      window.addEventListener("resize", onWindowResize);
    };
  
    function Particle(x, y, canvasItem) {
      const lifeSpan = Math.floor(Math.random() * 30 + 60);
      this.initialLifeSpan = lifeSpan; //
      this.lifeSpan = lifeSpan; //ms
      this.velocity = {
        x: (Math.random() < 0.5 ? -1 : 1) * (Math.random() / 2),
        y: Math.random() * 0.7 + 0.9,
      };
      this.position = { x: x, y: y };
      this.canv = canvasItem;
  
      this.update = function (context) {
        this.position.x += this.velocity.x;
        this.position.y += this.velocity.y;
        this.lifeSpan--;
  
        this.velocity.y += 0.02;
  
        const scale = Math.max(this.lifeSpan / this.initialLifeSpan, 0);
  
        context.drawImage(
          this.canv,
          this.position.x - (this.canv.width / 2) * scale,
          this.position.y - this.canv.height / 2,
          this.canv.width * scale,
          this.canv.height * scale
        );
      };
    }
  
    init();
  
    return {
      destroy: destroy
    }
  }








  export function followingDotCursor(options) {
    let hasWrapperEl = options && options.element;
    let element = hasWrapperEl || document.body;
  
    let width = window.innerWidth;
    let height = window.innerHeight;
    let cursor = { x: width / 2, y: width / 2 };
    let dot = new Dot(width / 2, height / 2, 10, 10);
    let canvas, context, animationFrame;
    let color = options?.color || "#323232a6";
  
    const prefersReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)"
    );
  
    // Re-initialise or destroy the cursor when the prefers-reduced-motion setting changes
    prefersReducedMotion.onchange = () => {
      if (prefersReducedMotion.matches) {
        destroy();
      } else {
        init();
      }
    };
  
    function init() {
      // Don't show the cursor trail if the user has prefers-reduced-motion enabled
      if (prefersReducedMotion.matches) {
        console.log(
          "This browser has prefers reduced motion turned on, so the cursor did not init"
        );
        return false;
      }
  
      canvas = document.createElement("canvas");
      context = canvas.getContext("2d");
      canvas.style.top = "0px";
      canvas.style.left = "0px";
      canvas.style.pointerEvents = "none";
  
      if (hasWrapperEl) {
        canvas.style.position = "absolute";
        element.appendChild(canvas);
        canvas.width = element.clientWidth;
        canvas.height = element.clientHeight;
      } else {
        canvas.style.position = "fixed";
        document.body.appendChild(canvas);
        canvas.width = width;
        canvas.height = height;
      }
  
      bindEvents();
      loop();
    }
  
    // Bind events that are needed
    function bindEvents() {
      element.addEventListener("mousemove", onMouseMove);
      window.addEventListener("resize", onWindowResize);
    }
  
    function onWindowResize(e) {
      width = window.innerWidth;
      height = window.innerHeight;
  
      if (hasWrapperEl) {
        canvas.width = element.clientWidth;
        canvas.height = element.clientHeight;
      } else {
        canvas.width = width;
        canvas.height = height;
      }
    }
  
    function onMouseMove(e) {
      if (hasWrapperEl) {
        const boundingRect = element.getBoundingClientRect();
        cursor.x = e.clientX - boundingRect.left;
        cursor.y = e.clientY - boundingRect.top;
      } else {
        cursor.x = e.clientX;
        cursor.y = e.clientY;
      }
    }
  
    function updateDot() {
      context.clearRect(0, 0, width, height);
  
      dot.moveTowards(cursor.x, cursor.y, context);
    }
  
    function loop() {
      updateDot();
      animationFrame = requestAnimationFrame(loop);
    }
  
    function destroy() {
      canvas.remove();
      cancelAnimationFrame(loop);
      element.removeEventListener("mousemove", onMouseMove);
      window.addEventListener("resize", onWindowResize);
    };
  
    function Dot(x, y, width, lag) {
      this.position = { x: x, y: y };
      this.width = width;
      this.lag = lag;
  
      this.moveTowards = function (x, y, context) {
        this.position.x += (x - this.position.x) / this.lag;
        this.position.y += (y - this.position.y) / this.lag;
  
        context.fillStyle = color;
        context.beginPath();
        context.arc(this.position.x, this.position.y, this.width, 0, 2 * Math.PI);
        context.fill();
        context.closePath();
      };
    }
  
    init();
  
    return {
      destroy: destroy
    }
  }








  export function ghostCursor(options) {
    let hasWrapperEl = options && options.element;
    let element = hasWrapperEl || document.body;
  
    let randomDelay = options && options.randomDelay;
    let minDelay = options && options.minDelay || 5;
    let maxDelay = options && options.maxDelay || 50;
    const lifeSpan = options && options.lifeSpan || 40;
  
    let width = window.innerWidth;
    let height = window.innerHeight;
    let cursor = { x: width / 2, y: width / 2 };
    let particles = [];
    let canvas, context, animationFrame;
  
    let baseImage = new Image();
    if (options && options.image) {
      baseImage.src = options.image;
    } else {
      baseImage.src =
        "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAwAAAATCAYAAACk9eypAAAAAXNSR0IArs4c6QAAACBjSFJNAAB6JgAAgIQAAPoAAACA6AAAdTAAAOpgAAA6mAAAF3CculE8AAAAhGVYSWZNTQAqAAAACAAFARIAAwAAAAEAAQAAARoABQAAAAEAAABKARsABQAAAAEAAABSASgAAwAAAAEAAgAAh2kABAAAAAEAAABaAAAAAAAAAEgAAAABAAAASAAAAAEAA6ABAAMAAAABAAEAAKACAAQAAAABAAAADKADAAQAAAABAAAAEwAAAAAChpcNAAAACXBIWXMAAAsTAAALEwEAmpwYAAABWWlUWHRYTUw6Y29tLmFkb2JlLnhtcAAAAAAAPHg6eG1wbWV0YSB4bWxuczp4PSJhZG9iZTpuczptZXRhLyIgeDp4bXB0az0iWE1QIENvcmUgNS40LjAiPgogICA8cmRmOlJERiB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiPgogICAgICA8cmRmOkRlc2NyaXB0aW9uIHJkZjphYm91dD0iIgogICAgICAgICAgICB4bWxuczp0aWZmPSJodHRwOi8vbnMuYWRvYmUuY29tL3RpZmYvMS4wLyI+CiAgICAgICAgIDx0aWZmOk9yaWVudGF0aW9uPjE8L3RpZmY6T3JpZW50YXRpb24+CiAgICAgIDwvcmRmOkRlc2NyaXB0aW9uPgogICA8L3JkZjpSREY+CjwveDp4bXBtZXRhPgpMwidZAAABqElEQVQoFY3SPUvDQBgH8BREpRHExYiDgmLFl6WC+AYmWeyLg4i7buJX8DMpOujgyxGvUYeCgzhUQUSKKLUS0+ZyptXh8Z5Ti621ekPyJHl+uftfomhaf9Ei5JyxXKfynyEA6EYcLHpwyflT958GAQ7DTABNHd8EbtDbEH2BD5QEQmi2mM8P/Iq+A0SzszEg+3sPjDnDdVEtQKQbMUidHD3xVzf6A9UDEmEm+8h9KTqTVUjT+vB53aHrCbAPiceYq1dQI1Aqv4EhMll0jzv+Y0yiRgCnLRSYyDQHVoqUXe4uKL9l+L7GXC4vkMhE6eW/AOJs9k583ORDUyXMZ8F5SVHVVnllmPNKSFagAJ5DofaqGXw/gHBYg51dIldkmknY3tguv3jOtHR4+MqAzaraJXbEhqHhcQlwGSOi5pytVQHZLN5s0WNe8HPrLYlFsO20RPHkImxsbmHdLJFI76th7Z4SeuF53hTeFLvhRCJRCTKZKxgdnRDbW+iozFJbBMw14/ElwGYc0egMBMFzT21f5Rog33Z7dX02GBm7WV5ZfT5Nn5bE3zuCDe9UxdTpNvK+5AAAAABJRU5ErkJggg==";
    }
  
    const prefersReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)"
    );
  
    // Re-initialise or destroy the cursor when the prefers-reduced-motion setting changes
    prefersReducedMotion.onchange = () => {
      if (prefersReducedMotion.matches) {
        destroy();
      } else {
        init();
      }
    };
  
    function init() {
      // Don't show the cursor trail if the user has prefers-reduced-motion enabled
      if (prefersReducedMotion.matches) {
        console.log(
          "This browser has prefers reduced motion turned on, so the cursor did not init"
        );
        return false;
      }
  
      canvas = document.createElement("canvas");
      context = canvas.getContext("2d");
      canvas.style.top = "0px";
      canvas.style.left = "0px";
      canvas.style.pointerEvents = "none";
  
      if (hasWrapperEl) {
        canvas.style.position = "absolute";
        element.appendChild(canvas);
        canvas.width = element.clientWidth;
        canvas.height = element.clientHeight;
      } else {
        canvas.style.position = "fixed";
        document.body.appendChild(canvas);
        canvas.width = width;
        canvas.height = height;
      }
  
      bindEvents();
      loop();
    }
  
    // Bind events that are needed
    function bindEvents() {
      element.addEventListener("mousemove", onMouseMove);
      element.addEventListener("touchmove", onTouchMove, { passive: true });
      element.addEventListener("touchstart", onTouchMove, { passive: true });
      window.addEventListener("resize", onWindowResize);
    }
  
    function onWindowResize(e) {
      width = window.innerWidth;
      height = window.innerHeight;
  
      if (hasWrapperEl) {
        canvas.width = element.clientWidth;
        canvas.height = element.clientHeight;
      } else {
        canvas.width = width;
        canvas.height = height;
      }
    }
  
    function onTouchMove(e) {
      if (e.touches.length > 0) {
        for (let i = 0; i < e.touches.length; i++) {
          addParticle(e.touches[i].clientX, e.touches[i].clientY, baseImage);
        }
      }
    }
  
    let getDelay = () => Math.floor(Math.random() * (maxDelay - minDelay + 1)) + minDelay;
    let lastTimeParticleAdded = Date.now(),
        interval = getDelay();
  
    function onMouseMove(e) {
      if (randomDelay) {
        if (lastTimeParticleAdded + interval > Date.now()) return;
        lastTimeParticleAdded = Date.now();
        interval = getDelay();
      }
  
      if (hasWrapperEl) {
        const boundingRect = element.getBoundingClientRect();
        cursor.x = e.clientX - boundingRect.left;
        cursor.y = e.clientY - boundingRect.top;
      } else {
        cursor.x = e.clientX;
        cursor.y = e.clientY;
      }
  
      addParticle(cursor.x, cursor.y, baseImage);
    }
  
    function addParticle(x, y, image) {
      particles.push(new Particle(x, y, image));
    }
  
    function updateParticles() {
      if (particles.length == 0) {
        return;
      }
      
      context.clearRect(0, 0, width, height);
  
      // Update
      for (let i = 0; i < particles.length; i++) {
        particles[i].update(context);
      }
  
      // Remove dead particles
      for (let i = particles.length - 1; i >= 0; i--) {
        if (particles[i].lifeSpan < 0) {
          particles.splice(i, 1);
        }
      }
  
      if (particles.length == 0) {
        context.clearRect(0, 0, width, height);
      }
    }
  
    function loop() {
      updateParticles();
      animationFrame = requestAnimationFrame(loop);
    }
  
    function destroy() {
      canvas.remove();
      cancelAnimationFrame(animationFrame);
      element.removeEventListener("mousemove", onMouseMove);
      element.removeEventListener("touchmove", onTouchMove);
      element.removeEventListener("touchstart", onTouchMove);
      window.addEventListener("resize", onWindowResize);
    };
  
    /**
     * Particles
     */
  
    function Particle(x, y, image) {
      this.initialLifeSpan = lifeSpan; //ms
      this.lifeSpan = lifeSpan; //ms
      this.position = { x: x, y: y };
  
      this.image = image;
  
      this.update = function (context) {
        this.lifeSpan--;
        const opacity = Math.max(this.lifeSpan / this.initialLifeSpan, 0);
  
        context.globalAlpha = opacity;
        context.drawImage(
          this.image,
          this.position.x, // - (this.canv.width / 2) * scale,
          this.position.y //- this.canv.height / 2,
        );
      };
    }
  
    init();
  
    return {
      destroy: destroy
    }
  }





  export function rainbowCursor(options) {
    let hasWrapperEl = options && options.element;
    let element = hasWrapperEl || document.body;
  
    let width = window.innerWidth;
    let height = window.innerHeight;
    let cursor = { x: width / 2, y: width / 2 };
    let particles = [];
    let canvas, context, animationFrame;
  
    const totalParticles = options?.length || 20;
    const colors = options?.colors || [
      "#FE0000",
      "#FD8C00",
      "#FFE500",
      "#119F0B",
      "#0644B3",
      "#C22EDC",
    ];
    const size = options?.size || 3;
  
    let cursorsInitted = false;
  
    const prefersReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)"
    );
  
    // Re-initialise or destroy the cursor when the prefers-reduced-motion setting changes
    prefersReducedMotion.onchange = () => {
      if (prefersReducedMotion.matches) {
        destroy();
      } else {
        init();
      }
    };
  
    function init() {
      // Don't show the cursor trail if the user has prefers-reduced-motion enabled
      if (prefersReducedMotion.matches) {
        console.log(
          "This browser has prefers reduced motion turned on, so the cursor did not init"
        );
        return false;
      }
  
      canvas = document.createElement("canvas");
      context = canvas.getContext("2d");
      canvas.style.top = "0px";
      canvas.style.left = "0px";
      canvas.style.pointerEvents = "none";
  
      if (hasWrapperEl) {
        canvas.style.position = "absolute";
        element.appendChild(canvas);
        canvas.width = element.clientWidth;
        canvas.height = element.clientHeight;
      } else {
        canvas.style.position = "fixed";
        document.body.appendChild(canvas);
        canvas.width = width;
        canvas.height = height;
      }
  
      bindEvents();
      loop();
    }
  
    // Bind events that are needed
    function bindEvents() {
      element.addEventListener("mousemove", onMouseMove);
      window.addEventListener("resize", onWindowResize);
    }
  
    function onWindowResize(e) {
      width = window.innerWidth;
      height = window.innerHeight;
  
      if (hasWrapperEl) {
        canvas.width = element.clientWidth;
        canvas.height = element.clientHeight;
      } else {
        canvas.width = width;
        canvas.height = height;
      }
    }
  
    function onMouseMove(e) {
      if (hasWrapperEl) {
        const boundingRect = element.getBoundingClientRect();
        cursor.x = e.clientX - boundingRect.left;
        cursor.y = e.clientY - boundingRect.top;
      } else {
        cursor.x = e.clientX;
        cursor.y = e.clientY;
      }
  
      if (cursorsInitted === false) {
        cursorsInitted = true;
        for (let i = 0; i < totalParticles; i++) {
          addParticle(cursor.x, cursor.y);
        }
      }
    }
  
    function addParticle(x, y, image) {
      particles.push(new Particle(x, y, image));
    }
  
    function updateParticles() {
      context.clearRect(0, 0, width, height);
      context.lineJoin = "round";
  
      let particleSets = [];
  
      let x = cursor.x;
      let y = cursor.y;
  
      particles.forEach(function (particle, index, particles) {
        let nextParticle = particles[index + 1] || particles[0];
  
        particle.position.x = x;
        particle.position.y = y;
  
        particleSets.push({ x: x, y: y });
  
        x += (nextParticle.position.x - particle.position.x) * 0.4;
        y += (nextParticle.position.y - particle.position.y) * 0.4;
      });
  
      colors.forEach((color, index) => {
        context.beginPath();
        context.strokeStyle = color;
  
        if (particleSets.length) {
          context.moveTo(
            particleSets[0].x,
            particleSets[0].y + index * (size - 1)
          );
        }
  
        particleSets.forEach((set, particleIndex) => {
          if (particleIndex !== 0) {
            context.lineTo(set.x, set.y + index * size);
          }
        });
  
        context.lineWidth = size;
        context.lineCap = "round";
        context.stroke();
      });
    }
  
    function loop() {
      updateParticles();
      animationFrame = requestAnimationFrame(loop);
    }
  
    function destroy() {
      canvas.remove();
      cancelAnimationFrame(animationFrame);
      element.removeEventListener("mousemove", onMouseMove);
      window.addEventListener("resize", onWindowResize);
    };
  
    function Particle(x, y) {
      this.position = { x: x, y: y };
    }
  
    init();
  
    return {
      destroy: destroy
    }
  }






  export function snowflakeCursor(options) {
    let hasWrapperEl = options && options.element;
    let element = hasWrapperEl || document.body;
  
    let possibleEmoji = ["❄️"];
    let width = window.innerWidth;
    let height = window.innerHeight;
    let cursor = { x: width / 2, y: width / 2 };
    let particles = [];
    let canvas, context, animationFrame;
  
    let canvImages = [];
  
    const prefersReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)"
    );
  
    // Re-initialise or destroy the cursor when the prefers-reduced-motion setting changes
    prefersReducedMotion.onchange = () => {
      if (prefersReducedMotion.matches) {
        destroy();
      } else {
        init();
      }
    };
  
    function init() {
      // Don't show the cursor trail if the user has prefers-reduced-motion enabled
      if (prefersReducedMotion.matches) {
        console.log(
          "This browser has prefers reduced motion turned on, so the cursor did not init"
        );
        return false;
      }
  
      canvas = document.createElement("canvas");
      context = canvas.getContext("2d");
  
      canvas.style.top = "0px";
      canvas.style.left = "0px";
      canvas.style.pointerEvents = "none";
  
      if (hasWrapperEl) {
        canvas.style.position = "absolute";
        element.appendChild(canvas);
        canvas.width = element.clientWidth;
        canvas.height = element.clientHeight;
      } else {
        canvas.style.position = "fixed";
        document.body.appendChild(canvas);
        canvas.width = width;
        canvas.height = height;
      }
  
      context.font = "12px serif";
      context.textBaseline = "middle";
      context.textAlign = "center";
  
      possibleEmoji.forEach((emoji) => {
        let measurements = context.measureText(emoji);
        let bgCanvas = document.createElement("canvas");
        let bgContext = bgCanvas.getContext("2d");
  
        bgCanvas.width = measurements.width;
        bgCanvas.height = measurements.actualBoundingBoxAscent * 2;
  
        bgContext.textAlign = "center";
        bgContext.font = "12px serif";
        bgContext.textBaseline = "middle";
        bgContext.fillText(
          emoji,
          bgCanvas.width / 2,
          measurements.actualBoundingBoxAscent
        );
  
        canvImages.push(bgCanvas);
      });
  
      bindEvents();
      loop();
    }
  
    // Bind events that are needed
    function bindEvents() {
      element.addEventListener("mousemove", onMouseMove);
      element.addEventListener("touchmove", onTouchMove, { passive: true });
      element.addEventListener("touchstart", onTouchMove, { passive: true });
      window.addEventListener("resize", onWindowResize);
    }
  
    function onWindowResize(e) {
      width = window.innerWidth;
      height = window.innerHeight;
  
      if (hasWrapperEl) {
        canvas.width = element.clientWidth;
        canvas.height = element.clientHeight;
      } else {
        canvas.width = width;
        canvas.height = height;
      }
    }
  
    function onTouchMove(e) {
      if (e.touches.length > 0) {
        for (let i = 0; i < e.touches.length; i++) {
          addParticle(
            e.touches[i].clientX,
            e.touches[i].clientY,
            canvImages[Math.floor(Math.random() * canvImages.length)]
          );
        }
      }
    }
  
    function onMouseMove(e) {
      if (hasWrapperEl) {
        const boundingRect = element.getBoundingClientRect();
        cursor.x = e.clientX - boundingRect.left;
        cursor.y = e.clientY - boundingRect.top;
      } else {
        cursor.x = e.clientX;
        cursor.y = e.clientY;
      }
  
      addParticle(
        cursor.x,
        cursor.y,
        canvImages[Math.floor(Math.random() * possibleEmoji.length)]
      );
    }
  
    function addParticle(x, y, img) {
      particles.push(new Particle(x, y, img));
    }
  
    function updateParticles() {
      if (particles.length == 0) {
        return;
      }
  
      context.clearRect(0, 0, width, height);
  
      // Update
      for (let i = 0; i < particles.length; i++) {
        particles[i].update(context);
      }
  
      // Remove dead particles
      for (let i = particles.length - 1; i >= 0; i--) {
        if (particles[i].lifeSpan < 0) {
          particles.splice(i, 1);
        }
      }
  
      if (particles.length == 0) {
        context.clearRect(0, 0, width, height);
      }
    }
  
    function loop() {
      updateParticles();
      animationFrame = requestAnimationFrame(loop);
    }
  
    function destroy() {
      canvas.remove();
      cancelAnimationFrame(animationFrame);
      element.removeEventListener("mousemove", onMouseMove);
      element.removeEventListener("touchmove", onTouchMove);
      element.removeEventListener("touchstart", onTouchMove);
      window.addEventListener("resize", onWindowResize);
    };
  
    /**
     * Particles
     */
  
    function Particle(x, y, canvasItem) {
      const lifeSpan = Math.floor(Math.random() * 60 + 80);
      this.initialLifeSpan = lifeSpan; //
      this.lifeSpan = lifeSpan; //ms
      this.velocity = {
        x: (Math.random() < 0.5 ? -1 : 1) * (Math.random() / 2),
        y: 1 + Math.random(),
      };
      this.position = { x: x, y: y };
      this.canv = canvasItem;
  
      this.update = function (context) {
        this.position.x += this.velocity.x;
        this.position.y += this.velocity.y;
        this.lifeSpan--;
  
        this.velocity.x += ((Math.random() < 0.5 ? -1 : 1) * 2) / 75;
        this.velocity.y -= Math.random() / 300;
  
        const scale = Math.max(this.lifeSpan / this.initialLifeSpan, 0);
  
        const degrees = 2 * this.lifeSpan;
        const radians = degrees * 0.0174533; // not perfect but close enough
  
        context.translate(this.position.x, this.position.y);
        context.rotate(radians);
  
        context.drawImage(
          this.canv,
          (-this.canv.width / 2) * scale,
          -this.canv.height / 2,
          this.canv.width * scale,
          this.canv.height * scale
        );
  
        context.rotate(-radians);
        context.translate(-this.position.x, -this.position.y);
      };
    }
  
    init();
  
    return {
      destroy: destroy
    }
  }








// The springy emoji effect has been translated over from this old
// code, to modern js & canvas
// - http://www.yaldex.com/FSMessages/ElasticBullets.htm
export function springyEmojiCursor(options) {
    let emoji = (options && options.emoji) || "🤪";
    let hasWrapperEl = options && options.element;
    let element = hasWrapperEl || document.body;
  
    let nDots = 7;
    let DELTAT = 0.01;
    let SEGLEN = 10;
    let SPRINGK = 10;
    let MASS = 1;
    let GRAVITY = 50;
    let RESISTANCE = 10;
    let STOPVEL = 0.1;
    let STOPACC = 0.1;
    let DOTSIZE = 11;
    let BOUNCE = 0.7;
  
    let width = window.innerWidth;
    let height = window.innerHeight;
    let cursor = { x: width / 2, y: width / 2 };
    let particles = [];
    let canvas, context, animationFrame;
  
    let emojiAsImage;
  
    const prefersReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)"
    );
  
    // Re-initialise or destroy the cursor when the prefers-reduced-motion setting changes
    prefersReducedMotion.onchange = () => {
      if (prefersReducedMotion.matches) {
        destroy();
      } else {
        init();
      }
    };
  
    function init() {
      // Don't show the cursor trail if the user has prefers-reduced-motion enabled
      if (prefersReducedMotion.matches) {
        console.log(
          "This browser has prefers reduced motion turned on, so the cursor did not init"
        );
        return false;
      }
  
      canvas = document.createElement("canvas");
      context = canvas.getContext("2d");
      canvas.style.top = "0px";
      canvas.style.left = "0px";
      canvas.style.pointerEvents = "none";
  
      if (hasWrapperEl) {
        canvas.style.position = "absolute";
        element.appendChild(canvas);
        canvas.width = element.clientWidth;
        canvas.height = element.clientHeight;
      } else {
        canvas.style.position = "fixed";
        document.body.appendChild(canvas);
        canvas.width = width;
        canvas.height = height;
      }
  
      // Save emoji as an image for performance
      context.font = "16px serif";
      context.textBaseline = "middle";
      context.textAlign = "center";
  
      let measurements = context.measureText(emoji);
      let bgCanvas = document.createElement("canvas");
      let bgContext = bgCanvas.getContext("2d");
  
      bgCanvas.width = measurements.width;
      bgCanvas.height = measurements.actualBoundingBoxAscent * 2;
  
      bgContext.textAlign = "center";
      bgContext.font = "16px serif";
      bgContext.textBaseline = "middle";
      bgContext.fillText(
        emoji,
        bgCanvas.width / 2,
        measurements.actualBoundingBoxAscent
      );
  
      emojiAsImage = bgCanvas;
  
      let i = 0;
      for (i = 0; i < nDots; i++) {
        particles[i] = new Particle(emojiAsImage);
      }
  
      bindEvents();
      loop();
    }
  
    // Bind events that are needed
    function bindEvents() {
      element.addEventListener("mousemove", onMouseMove);
      element.addEventListener("touchmove", onTouchMove, { passive: true });
      element.addEventListener("touchstart", onTouchMove, { passive: true });
      window.addEventListener("resize", onWindowResize);
    }
  
    function onWindowResize(e) {
      width = window.innerWidth;
      height = window.innerHeight;
  
      if (hasWrapperEl) {
        canvas.width = element.clientWidth;
        canvas.height = element.clientHeight;
      } else {
        canvas.width = width;
        canvas.height = height;
      }
    }
  
    function onTouchMove(e) {
      if (e.touches.length > 0) {
        if (hasWrapperEl) {
          const boundingRect = element.getBoundingClientRect();
          cursor.x = e.touches[0].clientX - boundingRect.left;
          cursor.y = e.touches[0].clientY - boundingRect.top;
        } else {
          cursor.x = e.touches[0].clientX;
          cursor.y = e.touches[0].clientY;
        }
      }
    }
  
    function onMouseMove(e) {
      if (hasWrapperEl) {
        const boundingRect = element.getBoundingClientRect();
        cursor.x = e.clientX - boundingRect.left;
        cursor.y = e.clientY - boundingRect.top;
      } else {
        cursor.x = e.clientX;
        cursor.y = e.clientY;
      }
    }
  
    function updateParticles() {
      canvas.width = canvas.width;
  
      // follow mouse
      particles[0].position.x = cursor.x;
      particles[0].position.y = cursor.y;
  
      // Start from 2nd dot
      for (let i = 1; i < nDots; i++) {
        let spring = new vec(0, 0);
  
        if (i > 0) {
          springForce(i - 1, i, spring);
        }
  
        if (i < nDots - 1) {
          springForce(i + 1, i, spring);
        }
  
        let resist = new vec(
          -particles[i].velocity.x * RESISTANCE,
          -particles[i].velocity.y * RESISTANCE
        );
  
        let accel = new vec(
          (spring.X + resist.X) / MASS,
          (spring.Y + resist.Y) / MASS + GRAVITY
        );
  
        particles[i].velocity.x += DELTAT * accel.X;
        particles[i].velocity.y += DELTAT * accel.Y;
  
        if (
          Math.abs(particles[i].velocity.x) < STOPVEL &&
          Math.abs(particles[i].velocity.y) < STOPVEL &&
          Math.abs(accel.X) < STOPACC &&
          Math.abs(accel.Y) < STOPACC
        ) {
          particles[i].velocity.x = 0;
          particles[i].velocity.y = 0;
        }
  
        particles[i].position.x += particles[i].velocity.x;
        particles[i].position.y += particles[i].velocity.y;
  
        let height, width;
        height = canvas.clientHeight;
        width = canvas.clientWidth;
  
        if (particles[i].position.y >= height - DOTSIZE - 1) {
          if (particles[i].velocity.y > 0) {
            particles[i].velocity.y = BOUNCE * -particles[i].velocity.y;
          }
          particles[i].position.y = height - DOTSIZE - 1;
        }
  
        if (particles[i].position.x >= width - DOTSIZE) {
          if (particles[i].velocity.x > 0) {
            particles[i].velocity.x = BOUNCE * -particles[i].velocity.x;
          }
          particles[i].position.x = width - DOTSIZE - 1;
        }
  
        if (particles[i].position.x < 0) {
          if (particles[i].velocity.x < 0) {
            particles[i].velocity.x = BOUNCE * -particles[i].velocity.x;
          }
          particles[i].position.x = 0;
        }
  
        particles[i].draw(context);
      }
    }
  
    function loop() {
      updateParticles();
      animationFrame = requestAnimationFrame(loop);
    }
  
    function destroy() {
      canvas.remove();
      cancelAnimationFrame(animationFrame);
      element.removeEventListener("mousemove", onMouseMove);
      element.removeEventListener("touchmove", onTouchMove);
      element.removeEventListener("touchstart", onTouchMove);
      window.addEventListener("resize", onWindowResize);
    };
  
    function vec(X, Y) {
      this.X = X;
      this.Y = Y;
    }
  
    function springForce(i, j, spring) {
      let dx = particles[i].position.x - particles[j].position.x;
      let dy = particles[i].position.y - particles[j].position.y;
      let len = Math.sqrt(dx * dx + dy * dy);
      if (len > SEGLEN) {
        let springF = SPRINGK * (len - SEGLEN);
        spring.X += (dx / len) * springF;
        spring.Y += (dy / len) * springF;
      }
    }
  
    function Particle(canvasItem) {
      this.position = { x: cursor.x, y: cursor.y };
      this.velocity = {
        x: 0,
        y: 0,
      };
  
      this.canv = canvasItem;
  
      this.draw = function (context) {
        context.drawImage(
          this.canv,
          this.position.x - this.canv.width / 2,
          this.position.y - this.canv.height / 2,
          this.canv.width,
          this.canv.height
        );
      };
    }
  
    init();
  
    return {
      destroy: destroy
    }
  }







// Text Flag
// via http://www.javascript-fx.com/mouse_trail/index.html (200X)
// via fun24.com (defunct, 199X)

export function textFlag(flagTextOption, speed, options) {
    let cursorOptions = options || {};
    let hasWrapperEl = options && options.element;
    let element = hasWrapperEl || document.body;
  
    let text = cursorOptions.text ? " " + options.text : flagTextOption;
    let color = options?.color || "#000000";
  
  
    let font = cursorOptions.font || "monospace";
    let textSize = cursorOptions.textSize || 12;
  
    let fontFamily = textSize + "px " + font;
  
    let gap = cursorOptions.gap || textSize + 2;
    let angle = 0;
    let radiusX = 2;
    let radiusY = 5;
    let charArray = [];
  
    let width = window.innerWidth;
    let height = window.innerHeight;
    let cursor = { x: width / 2, y: width / 2 };
  
    charArray = Array.from(text).map(char => ({ 
      letter: char, 
      x: width / 2, 
      y: width / 2 
    }));
  
    let canvas, context, animationFrame;
  
    const size = options?.size || 3;
  
    let cursorsInitted = false;
  
    const prefersReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)"
    );
  
    // Re-initialise or destroy the cursor when the prefers-reduced-motion setting changes
    prefersReducedMotion.onchange = () => {
      if (prefersReducedMotion.matches) {
        destroy();
      } else {
        init();
      }
    };
  
    function init() {
      // Don't show the cursor trail if the user has prefers-reduced-motion enabled
      if (prefersReducedMotion.matches) {
        console.log(
          "This browser has prefers reduced motion turned on, so the cursor did not init"
        );
        return false;
      }
  
      canvas = document.createElement("canvas");
      context = canvas.getContext("2d");
      canvas.style.top = "0px";
      canvas.style.left = "0px";
      canvas.style.pointerEvents = "none";
  
      if (hasWrapperEl) {
        canvas.style.position = "absolute";
        element.appendChild(canvas);
        canvas.width = element.clientWidth;
        canvas.height = element.clientHeight;
      } else {
        canvas.style.position = "fixed";
        document.body.appendChild(canvas);
        canvas.width = width;
        canvas.height = height;
      }
  
      bindEvents();
      loop();
    }
  
    // Bind events that are needed
    function bindEvents() {
      element.addEventListener("mousemove", onMouseMove);
      window.addEventListener("resize", onWindowResize);
    }
  
    function onWindowResize(e) {
      width = window.innerWidth;
      height = window.innerHeight;
  
      if (hasWrapperEl) {
        canvas.width = element.clientWidth;
        canvas.height = element.clientHeight;
      } else {
        canvas.width = width;
        canvas.height = height;
      }
    }
  
    function onMouseMove(e) {
      if (hasWrapperEl) {
        const boundingRect = element.getBoundingClientRect();
        cursor.x = e.clientX - boundingRect.left;
        cursor.y = e.clientY - boundingRect.top;
      } else {
        cursor.x = e.clientX;
        cursor.y = e.clientY;
      }
    }
  
    function updateParticles() {
        context.clearRect(0, 0, width, height);
        let newspeed = speed/10
        angle += newspeed;
      
        context.font = fontFamily;
      
        for (let i = 0; i < charArray.length; i++) {
          // Base position on cursor so it follows the mouse
          let baseX = cursor.x + i * gap;
          let baseY = cursor.y;
      
          // Apply sine wave for waving effect
          let waveY = baseY + Math.sin(angle + i * 0.5) * 15; // 15 = wave amplitude
      
          // Cycle colors like a rave snake
          let hue = (angle * 60 + i * 15) % 360;
          context.fillStyle = `hsl(${hue}, 100%, 50%)`;
      
          // Update char position and draw it
          charArray[i].x = baseX;
          charArray[i].y = waveY;
          context.fillText(charArray[i].letter, baseX, waveY);
        }
      }
      
  
    function loop() {
      updateParticles();
      animationFrame = requestAnimationFrame(loop);
    }
  
    function destroy() {
      canvas.remove();
      cancelAnimationFrame(animationFrame);
      element.removeEventListener("mousemove", onMouseMove);
      window.addEventListener("resize", onWindowResize);
    }
  
    init();
  
    return {
      destroy: destroy,
    };
  }







// The trailing cursor's easing has bene pulled from this demo
// - https://codepen.io/jakedeakin/full/MWKQVxX

export function trailingCursor(options) {
    let hasWrapperEl = options && options.element;
    let element = hasWrapperEl || document.body;
  
    let width = window.innerWidth;
    let height = window.innerHeight;
    let cursor = { x: width / 2, y: width / 2 };
    let particles = [];
    let canvas, context, animationFrame;
  
    const totalParticles = options?.particles || 15;
    const rate = options?.rate || 0.4;
    const baseImageSrc = options?.baseImageSrc || "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAwAAAATCAYAAACk9eypAAAAAXNSR0IArs4c6QAAACBjSFJNAAB6JgAAgIQAAPoAAACA6AAAdTAAAOpgAAA6mAAAF3CculE8AAAAhGVYSWZNTQAqAAAACAAFARIAAwAAAAEAAQAAARoABQAAAAEAAABKARsABQAAAAEAAABSASgAAwAAAAEAAgAAh2kABAAAAAEAAABaAAAAAAAAAEgAAAABAAAASAAAAAEAA6ABAAMAAAABAAEAAKACAAQAAAABAAAADKADAAQAAAABAAAAEwAAAAAChpcNAAAACXBIWXMAAAsTAAALEwEAmpwYAAABWWlUWHRYTUw6Y29tLmFkb2JlLnhtcAAAAAAAPHg6eG1wbWV0YSB4bWxuczp4PSJhZG9iZTpuczptZXRhLyIgeDp4bXB0az0iWE1QIENvcmUgNS40LjAiPgogICA8cmRmOlJERiB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiPgogICAgICA8cmRmOkRlc2NyaXB0aW9uIHJkZjphYm91dD0iIgogICAgICAgICAgICB4bWxuczp0aWZmPSJodHRwOi8vbnMuYWRvYmUuY29tL3RpZmYvMS4wLyI+CiAgICAgICAgIDx0aWZmOk9yaWVudGF0aW9uPjE8L3RpZmY6T3JpZW50YXRpb24+CiAgICAgIDwvcmRmOkRlc2NyaXB0aW9uPgogICA8L3JkZjpSREY+CjwveDp4bXBtZXRhPgpMwidZAAABqElEQVQoFY3SPUvDQBgH8BREpRHExYiDgmLFl6WC+AYmWeyLg4i7buJX8DMpOujgyxGvUYeCgzhUQUSKKLUS0+ZyptXh8Z5Ti621ekPyJHl+uftfomhaf9Ei5JyxXKfynyEA6EYcLHpwyflT958GAQ7DTABNHd8EbtDbEH2BD5QEQmi2mM8P/Iq+A0SzszEg+3sPjDnDdVEtQKQbMUidHD3xVzf6A9UDEmEm+8h9KTqTVUjT+vB53aHrCbAPiceYq1dQI1Aqv4EhMll0jzv+Y0yiRgCnLRSYyDQHVoqUXe4uKL9l+L7GXC4vkMhE6eW/AOJs9k583ORDUyXMZ8F5SVHVVnllmPNKSFagAJ5DofaqGXw/gHBYg51dIldkmknY3tguv3jOtHR4+MqAzaraJXbEhqHhcQlwGSOi5pytVQHZLN5s0WNe8HPrLYlFsO20RPHkImxsbmHdLJFI76th7Z4SeuF53hTeFLvhRCJRCTKZKxgdnRDbW+iozFJbBMw14/ElwGYc0egMBMFzT21f5Rog33Z7dX02GBm7WV5ZfT5Nn5bE3zuCDe9UxdTpNvK+5AAAAABJRU5ErkJggg==";
    let cursorsInitted = false;
  
    let baseImage = new Image();
    baseImage.src = baseImageSrc;
  
    const prefersReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)"
    );
  
    // Re-initialise or destroy the cursor when the prefers-reduced-motion setting changes
    prefersReducedMotion.onchange = () => {
      if (prefersReducedMotion.matches) {
        destroy();
      } else {
        init();
      }
    };
  
    function init() {
      // Don't show the cursor trail if the user has prefers-reduced-motion enabled
      if (prefersReducedMotion.matches) {
        console.log(
          "This browser has prefers reduced motion turned on, so the cursor did not init"
        );
        return false;
      }
  
      canvas = document.createElement("canvas");
      context = canvas.getContext("2d");
      canvas.style.top = "0px";
      canvas.style.left = "0px";
      canvas.style.pointerEvents = "none";
  
      if (hasWrapperEl) {
        canvas.style.position = "absolute";
        element.appendChild(canvas);
        canvas.width = element.clientWidth;
        canvas.height = element.clientHeight;
      } else {
        canvas.style.position = "fixed";
        document.body.appendChild(canvas);
        canvas.width = width;
        canvas.height = height;
      }
  
      bindEvents();
      loop();
    }
  
    // Bind events that are needed
    function bindEvents() {
      element.addEventListener("mousemove", onMouseMove);
      window.addEventListener("resize", onWindowResize);
    }
  
    function onWindowResize(e) {
      width = window.innerWidth;
      height = window.innerHeight;
  
      if (hasWrapperEl) {
        canvas.width = element.clientWidth;
        canvas.height = element.clientHeight;
      } else {
        canvas.width = width;
        canvas.height = height;
      }
    }
  
    function onMouseMove(e) {
      if (hasWrapperEl) {
        const boundingRect = element.getBoundingClientRect();
        cursor.x = e.clientX - boundingRect.left;
        cursor.y = e.clientY - boundingRect.top;
      } else {
        cursor.x = e.clientX;
        cursor.y = e.clientY;
      }
  
      if (cursorsInitted === false) {
        cursorsInitted = true;
        for (let i = 0; i < totalParticles; i++) {
          addParticle(cursor.x, cursor.y, baseImage);
        }
      }
    }
  
    function addParticle(x, y, image) {
      particles.push(new Particle(x, y, image));
    }
  
    function updateParticles() {
      context.clearRect(0, 0, width, height);
  
      let x = cursor.x;
      let y = cursor.y;
  
      particles.forEach(function (particle, index, particles) {
        let nextParticle = particles[index + 1] || particles[0];
  
        particle.position.x = x;
        particle.position.y = y;
        particle.move(context);
        x += (nextParticle.position.x - particle.position.x) * rate;
        y += (nextParticle.position.y - particle.position.y) * rate;
      });
    }
  
    function loop() {
      updateParticles();
      animationFrame = requestAnimationFrame(loop);
    }
  
    function destroy() {
      canvas.remove();
      cancelAnimationFrame(animationFrame);
      element.removeEventListener("mousemove", onMouseMove);
      window.addEventListener("resize", onWindowResize);
    };
  
    /**
     * Particles
     */
  
    function Particle(x, y, image) {
      this.position = { x: x, y: y };
      this.image = image;
  
      this.move = function (context) {
        context.drawImage(
          this.image,
          this.position.x, // - (this.canv.width / 2) * scale,
          this.position.y //- this.canv.height / 2,
        );
      };
    }
  
    init();
  
    return {
      destroy: destroy
    }
  }