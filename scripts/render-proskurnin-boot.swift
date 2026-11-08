import Foundation
import CoreGraphics
import CoreText
import ImageIO

let out = URL(fileURLWithPath: CommandLine.arguments[1], isDirectory: true)
let fm = FileManager.default
try fm.createDirectory(at: out.appendingPathComponent("intro"), withIntermediateDirectories: true)
try fm.createDirectory(at: out.appendingPathComponent("loop"), withIntermediateDirectories: true)
let space = CGColorSpaceCreateDeviceRGB()
func color(_ r: CGFloat, _ g: CGFloat, _ b: CGFloat, _ a: CGFloat = 1) -> CGColor {
    return CGColor(colorSpace: space, components: [r,g,b,a])!
}
func render(_ w: Int, _ h: Int, _ phase: Double, _ reveal: Double) -> CGImage {
    let c = CGContext(data: nil, width: w, height: h, bitsPerComponent: 8, bytesPerRow: w*4,
                      space: space, bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue)!
    c.setFillColor(color(0.004,0.007,0.018)); c.fill(CGRect(x:0,y:0,width:w,height:h))
    c.scaleBy(x:CGFloat(w)/1280, y:CGFloat(h)/720)
    let t = CGFloat(phase * 2 * Double.pi)
    let opacity = CGFloat(reveal)
    // Quiet coloured halos; the corners remain almost black.
    for (x,y,rgb) in [(CGFloat(435),CGFloat(350),[CGFloat(0.02),0.48,1.0]),
                       (CGFloat(830),CGFloat(365),[CGFloat(0.66),0.08,1.0])] {
        let grad = CGGradient(colorsSpace: space, colors: [color(rgb[0],rgb[1],rgb[2],0.13*opacity),color(0,0,0,0)] as CFArray, locations:[0,1])!
        c.drawRadialGradient(grad,startCenter:CGPoint(x:x,y:y),startRadius:0,
                             endCenter:CGPoint(x:x,y:y),endRadius:300,options:[])
    }
    let palette = [color(0.10,0.55,1),color(0.20,0.94,1),color(0.55,0.42,1),color(0.98,0.30,0.76)]
    let gradient = CGGradient(colorsSpace:space,colors:palette as CFArray,locations:[0,0.32,0.67,1])!
    // Two restrained luminous arcs behind the title.
    for upper in [false,true] {
        let path = CGMutablePath()
        let y: CGFloat = upper ? 415 : 285
        let bend = CGFloat(upper ? 60 : -60) + 8*sin(t)
        path.move(to:CGPoint(x:310,y:y))
        path.addCurve(to:CGPoint(x:970,y:y),control1:CGPoint(x:460,y:y+bend),control2:CGPoint(x:820,y:y-bend))
        for (width,alpha) in [(CGFloat(10),CGFloat(0.025)),(CGFloat(4),CGFloat(0.06)),(CGFloat(1),CGFloat(0.35))] {
            c.saveGState(); c.setAlpha(alpha*opacity); c.addPath(path.copy(strokingWithWidth:width,lineCap:.round,lineJoin:.round,miterLimit:1)); c.clip()
            c.drawLinearGradient(gradient,start:CGPoint(x:300,y:0),end:CGPoint(x:980,y:0),options:[]); c.restoreGState()
        }
    }
    let font = CTFontCreateWithName("HelveticaNeue-Medium" as CFString, 82, nil)
    let str = NSAttributedString(string:"Proskurnin TV",attributes:[NSAttributedString.Key(kCTFontAttributeName as String):font,
          NSAttributedString.Key(kCTForegroundColorFromContextAttributeName as String):true,
          NSAttributedString.Key(kCTKernAttributeName as String):1.2])
    let line = CTLineCreateWithAttributedString(str)
    let bounds = CTLineGetBoundsWithOptions(line,[.useGlyphPathBounds])
    let x = 640-bounds.midX, y = 360-bounds.midY + 5*(1-opacity)
    c.saveGState(); c.setAlpha(opacity)
    c.setShadow(offset:.zero,blur:15,color:color(0.13,0.48,1,0.35))
    c.setFillColor(color(0.65,0.85,1,0.30)); c.textPosition=CGPoint(x:x,y:y); CTLineDraw(line,c)
    c.restoreGState()
    c.saveGState(); c.setAlpha(opacity); c.textPosition=CGPoint(x:x,y:y); c.setTextDrawingMode(.clip); CTLineDraw(line,c)
    c.drawLinearGradient(gradient,start:CGPoint(x:300+25*sin(t),y:0),end:CGPoint(x:980+25*sin(t),y:0),options:[.drawsBeforeStartLocation,.drawsAfterEndLocation])
    // Very subtle sheen, with an exactly periodic loop.
    c.setFillColor(color(1,1,1,0.10+0.025*sin(t)));c.fill(CGRect(x:0,y:0,width:1280,height:720));c.restoreGState()
    return c.makeImage()!
}
func save(_ image:CGImage,_ url:URL,_ type:String) {
    let dest = CGImageDestinationCreateWithURL(url as CFURL,type as CFString,1,nil)!
    CGImageDestinationAddImage(dest,image,[kCGImageDestinationLossyCompressionQuality:0.35] as CFDictionary)
    precondition(CGImageDestinationFinalize(dest))
}
var frames:[CGImage]=[]
for i in 0..<8 {
    let u=Double(i)/7; let f=render(1280,720,0,u*u*(3-2*u))
    save(f,out.appendingPathComponent(String(format:"intro/%03d.png",i)),"public.png");frames.append(f)
}
for i in 0..<24 {
    let f=render(1280,720,Double(i)/24,1)
    save(f,out.appendingPathComponent(String(format:"loop/%03d.png",i)),"public.png");frames.append(f)
}
save(render(1920,1080,0,1),out.appendingPathComponent("bootlogo.jpg"),"public.jpeg")
save(render(1280,720,0,1),out.appendingPathComponent("preview.png"),"public.png")
let gif = CGImageDestinationCreateWithURL(out.appendingPathComponent("preview.gif") as CFURL,"com.compuserve.gif" as CFString,frames.count,nil)!
CGImageDestinationSetProperties(gif,[kCGImagePropertyGIFDictionary:[kCGImagePropertyGIFLoopCount:0]] as CFDictionary)
for f in frames {CGImageDestinationAddImage(gif,f,[kCGImagePropertyGIFDictionary:[kCGImagePropertyGIFDelayTime:0.05]] as CFDictionary)}
precondition(CGImageDestinationFinalize(gif))
print("Rendered Proskurnin TV: 1920x1080 JPEG, 32 animation frames at 1280x720, GIF preview")
